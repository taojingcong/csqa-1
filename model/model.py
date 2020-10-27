from .layers import AttentionMerge

import torch
import torch.nn as nn
import torch.nn.functional as F

from transformers.modeling_albert import AlbertPreTrainedModel
from transformers.modeling_albert import AlbertModel
from .kbert import KBERT


class Model(AlbertPreTrainedModel):
    """
    AlBert-AttentionMerge-Classifier

    1. self.forward(input_ids, attention_mask, token_type_ids, label)
    2. self.predict(input_ids, attention_mask, token_type_ids)
    """
    def __init__(self, config):
        super(Model, self).__init__(config)
        self.kbert = False

        if self.kbert:
            self.albert = KBERT(config)
        else:
            self.albert = AlbertModel(config)            

        self.att_merge = AttentionMerge(
            config.hidden_size, 1024, 0.1)

        self.scorer = nn.Sequential(
            #nn.Dropout(0.05),
            nn.Linear(config.hidden_size, 1)
        )


        self.init_weights()

    def merge(self,value):
        h1=nn.Linear(value.shape[2],1).cuda(0)
        h2=nn.Linear(value.shape[1],1).cuda(0)

        res=h1(value).view(value.shape[0],-1)
        res=h2(res).view(-1,5)
        res=F.softmax(res,dim=1)
        return res


    def score(self, h1, h2, h3, h4, h5):
        """
        h1, h2: [B, H] => logits: [B, 2]
        """
        logits1 = self.scorer(h1)
        logits2 = self.scorer(h2)
        logits3 = self.scorer(h3)
        logits4 = self.scorer(h4)
        logits5 = self.scorer(h5)
        logits = torch.cat((logits1, logits2, logits3, logits4, logits5), dim=1)
        return logits

    def forward(self, idx, input_ids, attention_mask, token_type_ids, labels):
        """
        input_ids: [B, 5, L]
        labels: [B, ]
        """
        # logits: [B, 5]
        logits = self._forward(idx, input_ids, attention_mask, token_type_ids)
        loss = F.cross_entropy(logits, labels)

        with torch.no_grad():
            logits = F.softmax(logits, dim=1)
            predicts = torch.argmax(logits, dim=1)
            right_num = torch.sum(predicts == labels)

        return loss, right_num, self._to_tensor(idx.size(0), idx.device)

    def _forward(self, idx, input_ids, attention_mask, token_type_ids):
        # [B, 2, L] => [B*2, L]
        flat_input_ids = input_ids.view(-1, input_ids.size(-1))#[40,41]
        flat_attention_mask = attention_mask.view(-1, attention_mask.size(-1))
        flat_token_type_ids = token_type_ids.view(-1, token_type_ids.size(-1))

        outputs = self.albert(
            input_ids=flat_input_ids,
            attention_mask=flat_attention_mask,
            token_type_ids=flat_token_type_ids
        )#outputs[0]=[40,41,4096]
        
        if self.kbert:
            flat_attention_mask = self.albert.get_attention_mask()
        
        # outputs[0]: [B*cls_num, L, H] => [B*cls_num, H]
        h12 = self.att_merge(outputs[0], flat_attention_mask)

        #merge
        #logits=self.merge(outputs[0])

        # [B*5, H] => [B*5, 1] => [B, 5]
        logits = self.scorer(h12).view(-1, 5)

        return logits

    def predict(self, idx, input_ids, attention_mask, token_type_ids):
        """
        return: [B, 2]
        """
        return self._forward(idx, input_ids, attention_mask, token_type_ids)

    def _to_tensor(self, it, device): return torch.tensor(it, device=device, dtype=torch.float)
