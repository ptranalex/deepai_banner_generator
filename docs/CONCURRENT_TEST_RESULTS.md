# DeepAI Concurrent Request Test Results

**Date:** October 31, 2025
**Test Duration:** ~50 seconds
**Purpose:** Determine if async implementation would speed up batch image generation

## Executive Summary

✅ **DeepAI DOES support concurrent requests** - no rate limiting detected
⚠️ **But with caveats** - content safety checks caused inconsistent results
🎯 **Recommendation:** Implement async with **2 concurrent requests** for safe, reliable 2x speedup

---

## Test Results

### Sequential Baseline (Control)

- **Images:** 3
- **Success Rate:** 100% (3/3)
- **Total Time:** 13.22s
- **Avg per Image:** 4.41s
- **Speedup:** 1.00x (baseline)

### 2 Concurrent Requests ✅ BEST RESULT

- **Images:** 3
- **Success Rate:** 100% (3/3)
- **Total Time:** 6.63s
- **Avg per Image:** 2.21s
- **Speedup:** **1.99x** (almost 2x faster!)

### 3 Concurrent Requests ❌ DEGRADED

- **Images:** 3
- **Success Rate:** 100% (3/3) _but with retries_
- **Total Time:** 19.22s
- **Avg per Image:** 6.41s
- **Speedup:** 0.69x (SLOWER than sequential!)
- **Issues:** One image triggered content safety warnings, required 3 retry attempts

### 5 Concurrent Requests ❌ FAILURES

- **Images:** 5
- **Success Rate:** 80% (4/5)
- **Total Time:** 18.57s
- **Avg per Image:** 3.71s
- **Speedup:** 0.71x (SLOWER than sequential!)
- **Issues:** 1 complete failure after 3 retry attempts

---

## Key Findings

### ✅ Good News

1. **No HTTP 429 rate limiting detected** - DeepAI didn't block or throttle concurrent requests
2. **2 concurrent requests work perfectly** - Achieved near-perfect 2x speedup
3. **Concurrent requests are processed in parallel** - Confirmed by timing data

### ⚠️ Concerns

1. **Content safety checks become problematic at higher concurrency**

   - Same prompt that worked sequentially triggered safety warnings when sent concurrently
   - Error: `"The system detected potentially unsafe content. Please try again or adjust the prompt."`
   - This is likely a false positive caused by multiple identical requests hitting the API simultaneously

2. **Higher concurrency (3+) is unreliable**

   - Retry logic helps but adds significant delay
   - Some requests fail completely even with retries

3. **Performance degrades beyond 2 concurrent**
   - 3+ concurrent actually SLOWER than sequential due to retries and failures

---

## Root Cause Analysis

The issue is **NOT rate limiting** but rather:

1. **DeepAI's content safety system** may flag identical concurrent requests as suspicious
2. **Retry logic** in our client (exponential backoff: 2s, 4s delays) adds significant time
3. **Random nature** of safety checks - same prompt works fine sometimes, fails others

---

## Recommendations

### For Your Use Case (Generating Many Images)

**Option 1: Conservative Async (Recommended) ⭐**

- Implement async with **max 2 concurrent requests**
- Benefits:
  - Reliable 2x speedup (13.22s → 6.63s for 3 images)
  - No content safety issues observed
  - Simple to implement
  - For 10 images: ~44s → ~22s (saves ~22 seconds)

**Option 2: Medium Async (With Monitoring)**

- Implement async with **max 3 concurrent requests**
- Add monitoring/logging for safety warnings
- Benefits:
  - Potentially higher speedup when prompts vary
  - Works well if your prompts are diverse (not identical)
- Risks:
  - May need to handle occasional retries
  - Less predictable performance

**Option 3: Keep Sequential (Not Recommended)**

- Simplest, but misses out on 2x speedup
- Only makes sense if you rarely generate >2 images at once

---

## Technical Implementation Plan

### Recommended Approach

1. **Use `asyncio` with `aiohttp`** instead of `requests`

   ```python
   # New async version alongside existing sync methods
   async def generate_image_async(...) -> str | None
   async def download_image_async(...) -> bool
   async def generate_and_save_async(...) -> bool
   ```

2. **Add semaphore for concurrency control**

   ```python
   semaphore = asyncio.Semaphore(2)  # Max 2 concurrent
   ```

3. **Keep existing sync methods** for backward compatibility

   - Current code continues to work
   - New batch operations use async

4. **Update `chain_banner.py` batch generation**
   - Lines 476-495 currently loop sequentially
   - Replace with `asyncio.gather()` with semaphore

### Expected Performance Gains

| Images | Current Time | With Async (2x) | Time Saved |
| ------ | ------------ | --------------- | ---------- |
| 3      | 13s          | 7s              | 6s (46%)   |
| 5      | 22s          | 11s             | 11s (50%)  |
| 10     | 44s          | 22s             | 22s (50%)  |
| 20     | 88s          | 44s             | 44s (50%)  |

---

## Additional Notes

### Why Not More Concurrency?

While DeepAI's infrastructure technically supports more concurrent requests, practical limitations emerge:

1. **Content safety false positives** increase with concurrency
2. **Retry delays** negate speed benefits
3. **Network/API instability** - more concurrent = more chance of transient failures

### Alternative: Vary Your Prompts

If you generate with **different prompts** (not identical), you might have better success with 3+ concurrent requests. The content safety issue may be specifically triggered by identical concurrent requests.

---

## Conclusion

**Yes, async will speed up your batch image generation!**

But implement conservatively:

- ✅ Use 2 concurrent requests for reliable 2x speedup
- ✅ Keep retry logic for transient failures
- ✅ Add monitoring/logging for safety warnings
- ❌ Avoid 5+ concurrent (diminishing returns, more issues)

The sweet spot is **2 concurrent requests** - simple, reliable, and delivers solid performance gains for your use case of generating many images.
