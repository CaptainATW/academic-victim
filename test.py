class Solution:
    def mergeAlternately(self, word1: str, word2: str) -> str:
        result = ""
        minimum = min(len(word1),len(word2))
        for i in range(minimum):
            result+=word1[i]
            result+=word2[i]
        return result

def main():
    solution = Solution()
    
    print(solution.mergeAlternately("abc", "cbd"))

if __name__ == "__main__":
    main()
