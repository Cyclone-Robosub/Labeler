# SAM2 Multi-Object Mask Selection Fix

## Problem Identified
When annotating multiple objects, clicking on the second (or subsequent) object would only change the mask color of the first object, rather than generating a new mask for the correct object.

## Root Cause
The `select_objects` method in `src/labeler/model.py` was always returning `out_mask_logits[0]` (the first mask), regardless of which object was being annotated.

**SAM2 Behavior**: When `add_new_points_or_box` is called, it returns:
- `out_obj_ids`: Array of ALL object IDs that have masks (e.g., `[2, 3, 5]`)
- `out_mask_logits`: Array of corresponding masks in the same order

**Previous Code Issue**:
```python
# Always returned the first mask (index 0)
return out_obj_ids, (out_mask_logits[0] > 0.0).cpu().numpy()
```

**Problem**: If you were adding points to object ID 3, it would return the mask for object ID 2 (first in the array).

## Solution Implemented
Modified `select_objects` to find the correct mask index for the specific object being annotated:

```python
def select_objects(self, points, labels, ann_obj_id, ann_frame_idx=0):
    _, out_obj_ids, out_mask_logits = self.predictor.add_new_points_or_box(
        inference_state=self.inference_state,
        frame_idx=ann_frame_idx,
        obj_id=ann_obj_id,
        points=points,
        labels=labels,
    )

    # Find the mask for the specific object ID we're working with
    mask_idx = None
    for i, obj_id in enumerate(out_obj_ids):
        if obj_id == ann_obj_id:
            mask_idx = i
            break
    
    if mask_idx is None:
        raise ValueError(f"Object ID {ann_obj_id} not found in returned masks")
    
    return out_obj_ids, (out_mask_logits[mask_idx] > 0.0).cpu().numpy()
```

## How It Works Now
1. **Object 1 (ID=2)**: Click points → SAM2 returns `[2]` and `[mask_for_2]` → Index 0 → Correct mask
2. **Object 2 (ID=3)**: Click points → SAM2 returns `[2, 3]` and `[mask_for_2, mask_for_3]` → Find index 1 → Correct mask  
3. **Object 3 (ID=5)**: Click points → SAM2 returns `[2, 3, 5]` and `[mask_for_2, mask_for_3, mask_for_5]` → Find index 2 → Correct mask

## Expected Behavior After Fix
- ✅ **Object 1**: Click → Generate blue mask for object 1
- ✅ **Object 2**: Click → Generate green mask for object 2 (not blue)
- ✅ **Object 3**: Click → Generate red mask for object 3 (not blue or green)
- ✅ **Multi-point**: Additional clicks on any object update only that object's mask
- ✅ **Error Handling**: Clear error if object ID not found in SAM2 response

## Testing Workflow
```
1. Load video
2. Add object "car" 
3. Add object "person"
4. Select "car" → click point → see blue mask
5. Select "person" → click point → see green mask (NEW MASK, not blue)
6. Select "car" → click another point → blue mask updates
7. Select "person" → click another point → green mask updates
```

## Error Prevention
Added validation to ensure the requested object ID exists in SAM2's response:
- If SAM2 doesn't return a mask for the requested object ID → Clear error message
- Prevents silent failures or wrong mask returns
- Helps debug SAM2 integration issues

This fix ensures that each object gets its own properly generated mask, enabling true multi-object annotation workflows as intended.
