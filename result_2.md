
'''
输入格式为initial_question [SEP] temp
当含有subject为question_concept，object为choice_concept的三元组时，temp = subject relations object
否则，temp = question_concept [SEP] choice_concept
其中，如果没有subject为question_concept，object为choice_concept的三元组时，会选择一个subject为choice_concept的三元组，
三元组选择策略，对每一个concept获取到的三元组，对其获取到的三元组进行关系权重评分，权重为其数量的倒数，最后按照三元组的weight、关系的权重、以及不同rel在数据集中比例(按照论文中所述)乘积作为最终的权重得分，选择得分最高的一个三元组
模型为conceptnet/weight_rel_key
without apex
accuracy:0.8239
batch_size:8
step:5
'''

