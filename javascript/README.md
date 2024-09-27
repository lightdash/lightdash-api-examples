# How to run these scripts

## Install dependencies

`yarn` 

or 

`npm i`


## Update the variables 

Update the varaibles in each script you want to run, like: 

```
const projectUuid = `3675b69e-8324-4110-bdca-059031aa8da3`
const apiKey = '<my-api-key>'
```

Find how to generate an API token https://docs.lightdash.com/references/personal_tokens

## Run the code

If you want to review the changes first, keep `test=true` in the script variables. If you're happy with the output, change this to `test=false` and run it again to perform changes against your project. 

```
node rename_models_in_charts.js
```

