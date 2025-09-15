# SceneLinter Pro Cookbook

Welcome to the advanced guide for **SceneLinter Pro**! The purpose of this document is to teach you how to create powerful, custom rules using the full capabilities of MaxScript. With this guide, you can check and control any aspect of your 3ds Max scene.

---
## ## Understanding the Rule Editor

Each rule is composed of several key parts:

* **Rule Name:** A descriptive name for your rule (e.g., "Check Render Resolution").
* **Condition Type:** The main engine of your rule. It determines what kind of comparison will be performed.
* **MaxScript Target/Prop:** The MaxScript command or expression that extracts the desired value from the scene. This is the heart of your rule.
* **Expected Value:** The value you expect the result of the above command to be.
* **Error Message:** The message that is displayed to the user if the rule fails.
* **Auto-Fix Script:** A MaxScript command that runs to automatically fix the error (optional).

---
## ## Condition Types Explained

* **`property_not_empty`**
    * **Use:** Checks if the target value is empty or undefined.
    * **Example:** Perfect for ensuring a Render Output Path has been set.

* **`min_value` / `max_value`**
    * **Use:** Checks if a numeric target value is less than a minimum or greater than a maximum.
    * **Example:** Ensuring the render width is at least `1920` pixels.

* **`property_equals`**
    * **Use:** Checks for exact equality between the target value and the expected value (this comparison is case-insensitive).
    * **Example:** Ensuring the active viewport is a camera (`true`).

* **`collection_property_all_match`**
    * **Use:** This advanced condition type checks a property on all members of a collection (e.g., all geometric objects).
    * **How to use:**
        * In the **MaxScript Target** field, enter the collection itself (e.g., `geometry`).
        * In the **Expected Value** field, enter the name of the boolean property you want to check on each member (e.g., `renderable`).
    * **Example:** Checking that all geometric objects are renderable.

---
## ## MaxScript Snippet Library

Here is a list of useful snippets to copy into the **MaxScript Target** and **Auto-Fix Script** fields.

### ### Snippets for "MaxScript Target"

#### Render Settings
```maxscript
-- Render Width
renderWidth

-- Render Height
renderHeight

-- Checks if render output is enabled (returns true or false)
(rendSaveFile == true and rendOutputFilename != "")

-- The name of the current render engine
renderers.current as string

Scene Stats

-- Total number of lights
lights.count

-- Total number of geometric objects
geometry.count

-- Total number of cameras
cameras.count

-- Total scene polygon count
polycount.total

-- Number of frozen objects in the scene
(for obj in objects where obj.isFrozen collect obj).count

Selected Object Properties (The $ symbol refers to the first selected object)

-- Name of the selected object
$.name

-- Radius of the selected object
$.radius

-- Wirecolor of the selected object
$.wirecolor
```
### Snippets for "Auto-Fix Script"
```

-- Opens the Render Output File selection dialog
maxOps.GetRenderOutputFilename()

-- Makes all geometric objects renderable
for obj in geometry where obj.renderable == false do obj.renderable = true

-- Unfreezes all frozen objects
for obj in objects where obj.isFrozen do obj.isFrozen = false

```

## Complete Example: Creating a New Rule
Let's create a rule that checks if any object has a default name (like Box001 or Sphere002).

Click the Add New button.

Fill in the fields as follows:

Rule Name: Check For Default Object Names

Condition Type: max_value
 
MaxScript Target/Prop:
```

(for o in objects where matchPattern o.name pattern:"*0*" collect o).count
(This counts the number of objects that have a number in their name)
```
```
Expected Value: 0
```
```
Error Message: Found objects with default numeric names. Please rename them.
```
```
Auto-Fix Script: (Leave blank)
```

With this guide, you and other users can customize SceneLinter Pro for any workflow and any need!
