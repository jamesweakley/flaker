# flaker
Faker for Snowflake! (AWS only)

This repository provides a way to leverage the popular [Faker](https://github.com/joke2k/faker) python library directly from a Snowflake query.

![fake names example](/example_names.png "Example")



The implementation uses a Snowflake External Function that calls out to the library via API Gateway, where it executes on a Lambda function.

You can use any of the standard providers listed [here](https://faker.readthedocs.io/en/master/providers.html).

It scales really nicely due to the batch processing of external functions, meaning you can generate large quantities of fake data in seconds.

## Installation

### Step 1 - Prerequisites

1) Install the [serverless framework](https://www.serverless.com/framework/docs/providers/aws/guide/installation/)

2) Follow the [setup guide](https://www.serverless.com/framework/docs/providers/aws/guide/credentials/) to authenticate to your AWS account, ready to deploy

### Step 2 - Deploy the API Gateway (sans Snowflake privileges)

Clone this repo, cd into it and run: `serverless deploy --config serverless-initial.yml --region ap-southeast-2`

(substitute your actual AWS region accordingly).

Once deployed, run: `serverless info -v --config serverless-initial.yml --region ap-southeast-2`

In the Stack Outputs section at the bottom, there are two pieces of information you need for the next step:
1. The ARN of the role for Snowflake to assume (see "SnowflakeExternalFunctionRole", starts with `arn:aws:iam::`)
2. The API endpoint for Snowflake to hit (see "ServiceEndpoint", starts with `https://`)


### Step 3 - Create the Snowflake API integration

Run the following SQL, with [the appropriate privileges](https://docs.snowflake.com/en/sql-reference/sql/create-api-integration.html#usage-notes)
```
create or replace api integration FLAKER_LAMBDA
    api_provider = aws_api_gateway
    api_aws_role_arn = '<The SnowflakeExternalFunctionRole value from step 2>'
    enabled = true
    api_allowed_prefixes = ('<The ServiceEndpoint value from step 2, with the /dev suffix removed>');

    describe integration FLAKER_LAMBDA;
```

The output from the above `describe` statement will return two pieces of information you need to update the AWS infrastructure:
1) The `API_AWS_IAM_USER_ARN` used to permit Snowflake to assume the AWS role that can call the AWS API gateway
2) The `API_AWS_EXTERNAL_ID ` used to restrict the scope of the above user to our specific api integration

### Step 4 - Update the AWS infrastructure to trust the Snowflake user

Back on your local command line, run:
`serverless deploy --region ap-southeast-2 --snowflake_user_arn <API_AWS_IAM_USER_ARN from step 3> --snowflake_external_id <API_AWS_EXTERNAL_ID from step 3>`

Wait for the stack to update successfully.

### Step 5 - Create the external functions in Snowflake

Run the following SQL:
```
create or replace external function FAKE(locales varchar,provider varchar,parameters varchar)
    returns variant
    VOLATILE
    api_integration = FLAKER_LAMBDA  
    MAX_BATCH_ROWS = 10000
    as '<The ServiceEndpoint value from step 2>'
    ;
create or replace external function FAKE(locales varchar,provider varchar)
    returns varchar
    VOLATILE 
    api_integration = FLAKER_LAMBDA
    MAX_BATCH_ROWS = 10000
    as '<The ServiceEndpoint value from step 2>'
    ;
    
```

## Examples

Generate 5000 fake names, in the US English locale:
```
select FAKE('en_US','name') as FAKE_NAME
    from table(generator(rowcount => 5000))
```

Generate 100 fake addresses, in the Japanese locale:
```
select FAKE('ja_JP','address') as FAKE_ADDRESS
    from table(generator(rowcount => 100))
```

Generate 100 fake profile attributes (name, job, company), and extract them from the returned variant column:
```
with FAKE_PROFILES as (
    select FAKE('en_AU','profile','name,job,company') as FAKE_PROFILE
    from table(generator(rowcount => 100))
    )
select FAKE_PROFILE:company::varchar,FAKE_PROFILE:job::varchar,FAKE_PROFILE:name::varchar
from FAKE_PROFILES
```