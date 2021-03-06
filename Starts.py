import EM
from NMI import nmi
import numpy as np
from utils import evaluateEM_NMI
from utils import maybeWrite

class starts:
    def __init__(self):
        bOptions = True
                 
    # get an cEM object that had the best log likelihood
    # of numRuns runs of EM given cData D and EM's #clusters = k
    def emLLRestarts(self,D,numRuns,k):
        centers = []
        maxEM = cEM(D)
        maxEM.bPPC = False
        maxEM.EM(k)
        maxLL = maxEM.dEMLikelihood
        for i in range(numRuns - 1):
            iteration = cEM(D)
            iteration.EM(k)
            ll = iteration.dEMLikelihood
            if maxLL < ll:
                maxLL = ll
                maxEM = iteration
        return maxEM

    # using the representative points metric, find good initial centers
    # given cData object D and emclusters as [ emcluster ],
    # and RepPts as RepPoints object (with options filled in)
    # and fp as file to write results each iteration
    def goodInitial (self,D,em,emclusters,RepPts,fp):
        # Consistent means all the midpoints are same with the center.
        constraints = []
        iters = 0

        indEMClusters = range(len(emclusters))
        lResetExclusions = []
        numUserQueries = 0
        for cl in emclusters:
            print ([D.data[i.index].cl for i in cl.midpoints],D.data[cl.center.index].cl)," ",cl.center.index
         
        while len(indEMClusters) != 0 and iters < 5:
            
            resetCenters = []
            
            for ind in indEMClusters[:]:
                cl = emclusters[ind]
                if(len(cl.midpoints) <= 1):
                    resetCenters.append(ind)
                    continue

                # simulate feedback from real classes
                realpoints = [D.data[i.index] for i in cl.midpoints]
                realcenter = D.data[cl.center.index]
                numUserQueries += len(realpoints) + 1
                # points in realpoints s.t. their real class is same as center
                rightclass = filter(lambda x: x.cl==realcenter.cl,realpoints)
                rightclass.append(realcenter)
                wrongclass = filter(lambda x: x.cl!=realcenter.cl,realpoints)

                # All the leftovers...
                if len(wrongclass) == 0:
                    indEMClusters.remove(ind)
                    lResetExclusions.extend( [x.index for x in rightclass] )
                else:
                    resetCenters.append(ind)
                    
                # Cross constraints between right and wrong classes.
                for i in rightclass:
                    for j in realpoints:
                        if j in wrongclass:
                            constraints.append([i.index,j.index,-2])
                        elif j!= i:
                            constraints.append([i.index,j.index,2])
                for i in constraints:
                    em.mCij[i[0]][i[1]] = i[2]
                    em.mCij[i[1]][i[0]] = i[2]

            # If all classes are not right, restart.
            em.resetSomeCenters(em.lInitialCenters,resetCenters,lResetExclusions)
            em.EM(len(emclusters))
            emclusters = RepPts.createClusters(em)
            RepPts.repPoints(em, emclusters)
            print "goodInitial iter nmi: ", evaluateEM_NMI(D,em)," ",iters
            iters += 1

            # queries,cons,likelihood,NMI
            maybeWrite(fp,
                       "%d,%d,%f,%f\n" % (numUserQueries,
                                          len(constraints),
                                          em.dEMLikelihood,
                                          evaluateEM_NMI(D,em) ) )
            print indEMClusters
            for cl in emclusters:
                print ([D.data[i.index].cl for i in cl.midpoints],D.data[cl.center.index].cl)," ",cl.center.index
            
        
        return em

    # returns a set of initial centers based on a clustering of
    # the centers of several initial clusterings
    # * D is the data (cData) object
    # * k is the number of classes (0 -> use #classes from D)
    def JLStartingPoint(D, k):
        if k == 0:
            k = len(D.classes)
        
        M = cEM(D)
        M.bPPC = False
        llCenters = []
        # get 20 different centers from running random-restarts of EM
        for iRestart in range(20):
            print "running EM ", iRestart, "..."
            M.lInitialCenters = []
            M.EM(k)
            llCenters.append(M.lCenters)

        # **** horrible hack - assumes this file exists because
        # it is not trivial to add a constructor that takes
        # a different type of data so a filename is needed
        D2 = cData("data/winenorm3_pyre.txt")
        D2.data = []
        print llCenters
        i = 0
        for center in llCenters:
            for V in center:
                D2.addDatum([0] + list(V), i)  # add 0 to beginning as class
                i += 1
            
        M2 = cEM(D2)
        M2.EM(k)
        return M2.lCenters
