nums = ['hkjsad714jajsd1', '34789nadsjdfs8asdf3', '3467jabbjfdsf81nnsad1']

for n in range(len(nums)):
    maxIdx = -1
    minIdx = float('inf')
    for j in range(len(nums[n])):
        try:
            myNum = int(nums[n][j])
            if j < minIdx:
                minIdx = j
            if j > maxIdx:
                maxIdx = j
        except ValueError:
            continue
    print(nums[n][minIdx], nums[n][maxIdx])
