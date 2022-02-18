import numpy as np
# Example of LagosDesc.txt below: (May include 100's of scenes). 
# S1A_IW_SLC__1SDV_20180313T052943_20180313T053012_020992_0240A7_005E
# S1A_IW_SLC__1SDV_20180325T052943_20180325T053013_021167_024636_8444
# S1A_IW_SLC__1SDV_20180406T052943_20180406T053013_021342_024BB1_0382
# S1A_IW_SLC__1SDV_20180418T052944_20180418T053013_021517_025130_BF34
# S1A_IW_SLC__1SDV_20180430T052944_20180430T053014_021692_0256A8_CF47
# S1A_IW_SLC__1SDV_20180512T052945_20180512T053015_021867_025C3F_40B0
# S1A_IW_SLC__1SDV_20180524T052945_20180524T053015_022042_0261CD_9A5C
# S1A_IW_SLC__1SDV_20180605T052946_20180605T053016_022217_026756_8F57
a = np.loadtxt('LagosDesc.txt', dtype=str)

ref = []
sec = []
pairlist= []

# This runs for 4 consecutive pairs. Note that this current code does not generate the last few possible pairings. 
for i in range(a.shape[0]-4):
	for j in [1,2,3,4]:
		ref.append(a[i])
		sec.append(a[i+j])
		pairlist.append(a[i]+"/"+a[i+j])

# This runs the next 2 consecutive pairs
# for i in range(a.shape[0]-2):
# 	for j in [1,2]:
# 		ref.append(a[i])
# 		sec.append(a[i+j])
# 		pairlist.append(a[i]+"/"+a[i+j])

np.savetxt("LagosDescRef4.txt", ref, fmt="%s", delimiter=' ')
np.savetxt("LagosDescSec4.txt", sec, fmt="%s", delimiter=' ')
np.savetxt("LagosDescList.txt", pairlist, fmt="%s", delimiter=' ')

#Then I save the Ref2 and Sec2 to the same location as the .sh file, and load them in the following way in the LagosArray.sh script:
# REF_GRANULE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" LagosDescRef4.txt)
# SND_GRANULE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" LagosDescSec4.txt)


print("Pair list has " + str(len(pairlist)) + " elements.")
