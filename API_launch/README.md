# Launch PW workflow from API

1. Set the PW_PLATFORM_HOST and PW_API_KEY environment variables in your running session.
2. Set the inputs of the workflow; `workflow_inputs.json` provided here is an example. You will likely need to change the compute resource ID. You can always get a fresh copy of the `.json` formatted workflow inputs from the `{} JSON` tab of a workflow's graphical user interface launch page.
3. Run the workflow with the following invocation:
```
# First argument is the PW username.
# Second argument is the workflow name.
python run_workflow.py <PW_USER> tiegcm workflow_inputs.json
```