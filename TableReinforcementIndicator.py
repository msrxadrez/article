import numpy as np
import pandas as pd
import random
import tensorflow as tf
import matplotlib.pyplot as plt
import sys
import os

from DiscretizedEnvironment import DiscretizedEnvironment
#from Environment import Environment

class TableReinforcementIndicator:

    def __init__(
        self,
        stock
    ):
        self.dataFrame = pd.read_csv(
            'spx_intraday.csv', index_col=0, header=[0, 1]
        ).sort_index(axis=1)[stock]

        self.priceData = np.array(self.dataFrame["close"])
        print len(self.priceData)
        print 0, self.priceData[1999], self.priceData[1500], self.priceData[1999] - self.priceData[1500]
        print 1, self.priceData[2999], self.priceData[2500], self.priceData[2999] - self.priceData[2500]
        print 2, self.priceData[3999], self.priceData[3500], self.priceData[3999] - self.priceData[3500]
        print 3, self.priceData[4999], self.priceData[4500], self.priceData[4999] - self.priceData[4500]
        print 4, self.priceData[5999], self.priceData[5500], self.priceData[5999] - self.priceData[5500]

        # Env Parameters
        n_input = 49 # Num states
        n_classes = 7 # Q-value for each action

        self.num_actions = n_classes
        self.num_states = n_input
        self.stock = stock

    def train(
        self,
        # Set learning hyper parameters
        learning_rate=0.8,
        y=.95,
        e=.01,
        initialization_period=10,
        initial_offset=2000,
        num_epochs=100,
        time_horizon=1000,
        verbose=False,
        test_number=0,
    ):
        #Initialize table with all zeros
        self.Q = np.zeros([self.num_states,self.num_actions])
        # Set learning parameters
        lr = learning_rate
        num_episodes = num_epochs
        #create lists to contain total rewards and steps per episode
        #jList = []
        rList = []
        self.env = DiscretizedEnvironment(
            self.dataFrame,
            initializationPeriod=initialization_period,
            initialOffset=initial_offset
        )

        for i in range(num_episodes):
            #Reset environment and get first new observation
            s = self.env.reset()
            rAll = 0
            d = False
            j = 0
            #The Q-Table learning algorithm
            while j < time_horizon:
                j+=1
                #Choose an action by greedily (with noise) picking from Q table
                a = np.argmax(self.Q[s,:])
                if np.random.rand(1) < e:
                    a = np.random.choice(self.env.action_space)
                #Get new state and reward from environment
                s1,r = self.env.step(a)
                #Update Q-Table with new knowledge
                self.Q[s,a] = self.Q[s,a] + lr*(r + y*np.max(self.Q[s1,:]) - self.Q[s,a])
                rAll += r
                s = s1

            if rAll > 1000:
                #Reduce chance of random action as we train the model.
                e = 1./((i/50) + 10)
            #jList.append(j)
            rList.append(rAll)

        if(verbose):
            plt.plot(rList)
            fig_name = './'+ self.stock + '/' + self.stock + '_trainT_' + str(test_number) + '.png'
            plt.savefig(fig_name)
            plt.close()
            #plt.show()
            print np.max(rList), np.min(rList), np.mean(rList)
            print (np.asarray(rList) > 0).sum()

        return np.mean(rList)

    def dev(
        self,
        random_iterations=100,
        dev_horizon = 500,
        initial_offset=2000,
    ):
        paramSet = []
        for i in range(random_iterations):
            #paratemers to train
            learning_rate = pow(10,-3*np.random.rand())
            e = pow(10,-2*np.random.rand()-1)
            y = 1 - pow(10,-2*np.random.rand()-1)
            initialization_period = int(round(25*np.random.rand()+5))

            paramSet.append({
                'learning_rate': learning_rate,
                'e': e,
                'y': y,
                'initialization_period': initialization_period,
                'initial_offset': initial_offset,
            })

        results = []
        for params in paramSet:
            #print 'training for params: ' + str(params)
            self.train(**params)
            results.append(self.test(dev_horizon))

        return paramSet[results.index(max(results))]

    def test(
        self,
        test_time_horizon,
        ignore_offset=0,
        verbose=False,
        test_number=0,
    ):
        Qout = self.Q
        predict = tf.argmax(Qout,1)
        s = self.env.getCurrentState()

        #create a list to contain total rewards
        rList = []
        rAll = 0
        rAllList = []
        init = tf.global_variables_initializer()
        with tf.Session() as sess:
            sess.run(init)
            for i in range(test_time_horizon):
                # Choose an action by from the Q-network
                a = np.argmax(self.Q[s,:])
                # Get new state and reward from environment
                s,r = self.env.step(a)
                if(i >= ignore_offset):
                    rAll += r
                    rAllList.append(rAll)
                    rList.append(r)

        if(verbose):
            plt.plot(rAllList)
            fig_name = './'+ self.stock + '/' + self.stock + '_testT_' + str(test_number) + '.png'
            plt.savefig(fig_name)
            plt.close()
            #plt.show()
            print np.max(rList), np.min(rList), np.mean(rList), np.max(rAllList)
            print (np.asarray(rList) > 0).sum()

        return np.sum(rList)

    def testSelected(
        self,
    ):
        if not os.path.exists(self.stock):
            os.makedirs(self.stock)

        orig_stdout = sys.stdout
        file_name = './'+ self.stock + '/' + self.stock + '_T.txt'
        f = open(file_name, 'w')
        sys.stdout = f

        allRes = []
        for i in range(5):
            print 'test ' + str(i)
            params = self.dev(dev_horizon=500, initial_offset=i*1000)
            print 'training with: ' + str(params)
            params['initial_offset'] = i*1000
            params['verbose'] = True
            params['test_number'] = i
            self.train(**params )
            res = self.test(1000,ignore_offset=500, verbose=True, test_number=i)
            allRes.append(res)
            print '\n'
        #plt.plot(allRes)
        #plt.show()
        print (np.asarray(allRes) > 0).sum()

        sys.stdout = orig_stdout
        f.close()
