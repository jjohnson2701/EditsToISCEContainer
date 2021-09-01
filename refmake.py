import numpy as np
import argparse

# #get directory information.
# def getparser():
#     # Parser to submit inputs for scripts. See Jul 27 Email from Jasmine
#     parser = argparse.ArgumentParser(description="Input list of pairs")
#     parser.add_argument('pairlist', type=str, help='home directory holding date pair folders. For example, add CameronP78list.txt after calling this script')
#     return parser
# parser = getparser()
# args = parser.parse_args()
# a= args.pairlist


a = np.loadtxt('LagosDesc.txt', dtype=str)

ref = []
sec = []
pairlist= []

# This runs for 4 consecutive pairs
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

#Then I save the Ref2 and Sec2 to the same location as the .sh file, and load them in the following way in the ChileArray.sh script:
# REF_GRANULE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" ChileP62Ref2.txt)
# SND_GRANULE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" ChileP62Sec2.txt)


print("Pair list has " + str(len(pairlist)) + " elements.")