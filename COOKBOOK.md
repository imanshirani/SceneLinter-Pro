# SceneLinter Pro Cookbook (v0.0.1)

Welcome to the advanced guide for **SceneLinter Pro**! The purpose of this document is to teach you how to create powerful, custom rules using the full capabilities of MaxScript. With this guide, you can check and control any aspect of your 3ds Max scene.

---
## ## Understanding the Rule Editor

Each rule is composed of several key parts:

* **Rule Name:** A descriptive name for your rule.
* **Condition Type:** The main engine of your rule, which determines the comparison logic.
* **MaxScript Target/Prop:** The MaxScript command that extracts a value from your scene.
* **Expected Value:** The value you expect the result to be.
* **Error Message:** The message displayed if the rule fails.
* **Auto-Fix Script:** An optional MaxScript command that runs to automatically fix the error.

---
## ## Condition Types Explained

* **`property_not_empty`**: Checks if a value is empty or not.
* **`min_value` / `max_value`**: Checks if a numeric value is above a minimum or below a maximum.
* **`property_equals`**: Checks for exact equality (case-insensitive).
* **`collection_property_all_match`**: Checks a boolean property on all members of a collection (e.g., checks if `renderable` is `true` for all `geometry`).

---
## ## MaxScript Cookbook (Snippet Library)

Here is a comprehensive list of useful snippets for the **MaxScript Target** and **Auto-Fix Script** fields.

### ### Render Settings

| Description                | MaxScript Target Snippet                               |
| -------------------------- | ------------------------------------------------------ |
| Render Width               | `renderWidth`                                          |
| Render Height              | `renderHeight`                                         |
| Render Output Enabled      | `(rendSaveFile == true and rendOutputFilename != "")`  |
| Current Render Engine      | `renderers.current as string`                          |
| Animation Frame Count      | `(timeConfiguration.animationRange.end - timeConfiguration.animationRange.start + 1)` |
| Atmospheric Effects Count  | `numAtmospherics()`                                    |

### ### Scene & Objects

| Description                        | MaxScript Target Snippet                                       | Auto-Fix Script Example                                           |
| ---------------------------------- | -------------------------------------------------------------- | ----------------------------------------------------------------- |
| Total Object Count                 | `objects.count`                                                |                                                                   |
| Total Polygon Count                | `polycount.total`                                              |                                                                   |
| Number of Frozen Objects           | `(for obj in objects where obj.isFrozen collect obj).count`    | `for obj in objects where obj.isFrozen do obj.isFrozen = false`   |
| Number of Hidden Objects           | `(for obj in objects where obj.isHidden collect obj).count`    | `for obj in objects where obj.isHidden do obj.isHidden = false` |
| Objects with Default Names         | `(for o in objects where matchPattern o.name pattern:"*0*" collect o).count` |                                                                   |

### ### Selected Object (`$`)

*The `$` symbol refers to the first selected object.*

| Description                  | MaxScript Target Snippet               |
| ---------------------------- | -------------------------------------- |
| Name of the selected object  | `$.name`                               |
| Class of the selected object | `classof $`                            |
| Number of vertices           | `$.verts.count`                        |
| Position of the selected object | `$.pos`                                |
| Wirecolor of the selected object | `$.wirecolor`                          |
| Has any Modifiers?           | `$.modifiers.count`                    |

### ### Modifiers (on selected object)

| Description                               | MaxScript Target Snippet                                |
| ----------------------------------------- | ------------------------------------------------------- |
| TurboSmooth Iterations                    | `$.modifiers[#TurboSmooth].iterations`                  |
| Shell Outer Amount                        | `$.modifiers[#Shell].outerAmount`                       |
| Number of subdivision levels in an Edit Poly modifier | `$.modifiers[#Edit_Poly].GetSubdivisionLevels()` |

### ### Materials & Textures

| Description                                      | MaxScript Target Snippet                                 | Auto-Fix Script Example                               |
| ------------------------------------------------ | -------------------------------------------------------- | ----------------------------------------------------- |
| Objects with no material assigned                | `(for o in geometry where o.material == undefined collect o).count` |                                                       |
| Number of Multi/Sub-Object materials in scene    | `(for m in sceneMaterials where isKindOf m MultiMaterial collect m).count` |                                                       |
| Number of missing texture maps in the scene      | `(getMissingMaps()).count`                               |                                                       |
| Bitmap nodes with Blur setting not equal to 1.0  | `(for t in (getClassInstances BitMapTexture) where t.blur != 1.0 collect t).count` | `for t in (getClassInstances BitMapTexture) do t.blur = 1.0` |

### ### System & Units

| Description                | MaxScript Target Snippet                               |
| -------------------------- | ------------------------------------------------------ |
| Current System Unit Scale  | `units.SystemScale`                                    |
| Current Display Unit       | `units.DisplayType`                                    |

---
## ## Complete Example: Checking TurboSmooth Iterations

Let's create a rule to ensure no object has a TurboSmooth modifier with more than 3 iterations.

1.  Click **Add New**.
2.  Fill in the fields:

    * **Rule Name:** `Check TurboSmooth Iterations`
    * **Condition Type:** `collection_property_all_match` (We need to slightly adapt this)
        * Actually, let's use a more direct approach for this one:
    * **Condition Type:** `max_value`
    * **MaxScript Target/Prop:**
        ```maxscript
        (local max_iter = 0; for o in geometry where isProperty o.modifiers #TurboSmooth do (max_iter = max max_iter o.modifiers[#TurboSmooth].iterations); max_iter)
        ```
        *(This complex script finds the maximum iteration value among all TurboSmooth modifiers in the scene)*
    * **Expected Value:** `3`
    * **Error Message:** `Found objects with TurboSmooth iterations greater than 3.`
    * **Auto-Fix Script:**
        ```maxscript
        for o in geometry where isProperty o.modifiers #TurboSmooth and o.modifiers[#TurboSmooth].iterations > 3 do o.modifiers[#TurboSmooth].iterations = 3
        ```
