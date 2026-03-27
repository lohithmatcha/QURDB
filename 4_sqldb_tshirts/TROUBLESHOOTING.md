# Troubleshooting Visualization

## Quick Diagnosis Steps

### Step 1: Install Dependencies
```bash
cd 4_sqldb_tshirts
pip install -r requirements.txt
```

**Key packages that must be installed:**
- `plotly>=5.17.0`
- `pandas>=2.0.0`
- `langchain-google-genai`

### Step 2: Test Visualization Helper
```bash
python test_visualization.py
```

If this runs without errors, the visualization helper is working correctly.

### Step 3: Run Your App and Check Debug Info
```bash
streamlit run main.py
```

**How to diagnose:**
1. Ask a question like "How many Nike t-shirts do we have?"
2. **Click on "🔍 Debug Info"** expander at the bottom
3. Look for:
   - Raw Database Result (what format is the data?)
   - Visualization Type (what chart type was selected?)
   - Has Chart (True/False?)
   - Metadata (what properties were detected?)

### Step 4: Common Issues & Solutions

#### Issue 1: "ModuleNotFoundError: No module named 'plotly'"
**Solution:**
```bash
pip install plotly pandas
```

#### Issue 2: Charts not showing, but no error message
**Possible causes:**
- Database result format not recognized
- Data is being filtered out
- Chart creation is failing silently

**Diagnosis:**
- Check Debug Info → Visualization Debug section
- Look for "Visualization Error" in Debug Info
- Check metadata to see what was detected

#### Issue 3: "Error displaying chart"
**Solution:**
- This means the chart was created but can't be displayed
- Check the error message in Debug Info
- Usually indicates a Plotly version issue

## Expected Behavior

### For Single Values
```
Question: "How many Nike shirts?"
→ Should show: Large metric card with the number
```

### For Comparisons
```
Question: "Which brand has the most stock?"
→ Should show: Bar chart comparing brands
```

### For Breakdowns
```
Question: "What's the breakdown by color?"
→ Should show: Pie chart or bar chart
```

## Debugging Tips

### Check the Database Result Format
The visualization system expects results in specific formats:

1. **Single value**: `[(98,)]` or `98`
2. **Multiple rows, single column**: `[(98,), (120,), (85,)]`
3. **Multiple rows, multiple columns**: `[('Nike', 98), ('Adidas', 120)]`

If your result format is different, it might not be recognized.

### Enable Verbose Logging

You can add this to your `main.py` to see what's happening:

```python
# Right after creating visualization
st.write(f"Debug: vis_result keys = {vis_result.keys() if vis_result else 'None'}")
st.write(f"Debug: has_chart = {has_chart}")
```

### Common Database Result Formats

SQLAlchemy typically returns results as:
```python
# Single value
[(Decimal('98'),)]

# Multiple columns
[('Nike', Decimal('98')), ('Adidas', Decimal('120'))]

# Single tuple
(Decimal('98'),)
```

## If Still Not Working

1. **Check Debug Info** - Always start here!
2. **Run test script**: `python test_visualization.py`
3. **Check requirements**: `pip list | grep plotly`
4. **Check Streamlit logs**: Look at terminal output when running the app

## Quick Fix: Force Table Display

If charts aren't working, you can temporarily force table display by modifying `visualization_helper.py`:

```python
# Around line 234, change:
return 'table'  # Force table for everything
```

This will at least show the data in a table format.

## Contact Support

If nothing works, share:
1. Output from Debug Info
2. Output from `python test_visualization.py`
3. Your question and the database result

