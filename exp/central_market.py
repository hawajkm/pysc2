import numpy as np
import Queue
import random
import json

def generate_data():
  # Randomly generate a set of (x,y) locations for SCVs and minerals
  scv_num  = 10
  min_num  = 10
  scvs     = {}
  minerals = {}

  for i in range(scv_num):
    x = round(random.random() * 10,2)
    y = round(random.random() * 10,2)
    t = round(random.random() * 50 + 20,2)
    scvs[i] = {'x':x , 'y':y,'tag':t}    

  for i in range(min_num):
    x = round(random.random() * 10,2)
    y = round(random.random() * 10,2)
    minerals[i] = {'x':x , 'y':y, 'p':0,'ID':i}

  #scvs[0] = {'x':2 , 'y':4,'tag':35}
  #scvs[1] = {'x':4 , 'y':4,'tag':53}    
  #scvs[2] = {'x':12 , 'y':10,'tag':88}    
  #minerals[0] = {'x':3 , 'y':6, 'p':0}
  #minerals[2] = {'x':8 , 'y':8, 'p':0}
  #minerals[1] = {'x':10 , 'y':10, 'p':0}

  return scvs, minerals

# Initialize 2D list of weights
# Rows = SCV ID
# Cols = Mineral ID
def init_weights(scvs,minerals):
  num_scv = len(scvs)
  num_min = len(minerals)
  weights = []
  
  for i in range(num_scv):
    temp = []
    for j in range(num_min):
      scv_x = scvs[i]['x']
      scv_y = scvs[i]['y']
      min_x = minerals[j]['x']
      min_y = minerals[j]['y']
      dist = pow(scv_x-min_x,2) + pow(scv_y-min_y,2)
      w = 1/float(dist) 
      temp.append(w)
    weights.append(temp)
    
  return weights

def auction(scvs,minerals,weights):
  # Initialize empty assignment dictionar S {mineral_id:scv_id}
  S = {}

  # Intialize queue to contain all bidders
  q = Queue.Queue(maxsize=len(scvs))

  for key in scvs:
    print(key)
    q.put(key)

  while(not q.empty()):
    i = q.get()  # Current SCV
    print("Current SCV: ", i)

    # Find mineral j that maximizes profit: weight_{ij} - p_j
    w_i = weights[i] # All weights for current SCV i
    print(w_i)
    profit = [w_i[ind] - minerals[ind]['p'] for ind in range(len(w_i))]
    print("profits for i: ", profit)
    j = profit.index(max(profit)) # Index of mineral with maximum profit
    v = profit[j]  # Profit of mineral[j]
    print("v: ",v) 
    
    # Find second highest profit
    del profit[j]  
    w = max(profit) # Second highest profit
    print("w: ",w)

    p_j = minerals[j]['p'] # Price of mineral with highest profit
    if (not j in S) or (S[j] != i):
      # Enqueue current owner of j into queue
      if j in S:
        curr_owner_id = S[j] 
        q.put(curr_owner_id)
      # SCV i now gets mineral j
      S[j] = i
      # Increase price of mineral j
      minerals[j]['p'] = p_j + (v-w)
      #print json.dumps(minerals, sort_keys=True, indent=4, separators=(',',': ')) 

  print("final:")
  print(S)
  

def main():
  scvs, minerals = generate_data()

  print json.dumps(scvs, sort_keys=True, indent=4, separators=(',',': ')) 
  print json.dumps(minerals, sort_keys=True, indent=4, separators=(',',': ')) 
  
  weights = init_weights(scvs,minerals)

  print("Weights: ", weights)

  auction(scvs,minerals,weights)

if __name__ == "__main__":
  main()
