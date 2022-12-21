# flaker
Faker for Snowflake!

This repository originally described a Snowflake External Function which invoked the [Faker](https://github.com/joke2k/faker) python library in an AWS Lambda function, directly from a Snowflake query. This older codebase and information can be found under the 'external_function' branch of this repo.

As of mid 2022, Snowflake now offer Python support natively on platform. This means that the new way to invoke Faker is as simple as:
```
create or replace function FAKE(locale varchar,provider varchar,parameters variant)
returns variant
language python
volatile
runtime_version = '3.8'
packages = ('faker','simplejson')
handler = 'fake'
as
$$
import simplejson as json
from faker import Faker
def fake(locale,provider,parameters):
  if type(parameters).__name__=='sqlNullWrapper':
    parameters = {}
  fake = Faker(locale=locale)
  return json.loads(json.dumps(fake.format(formatter=provider,**parameters), default=str))
$$;

```

You can use pretty much any of the standard providers listed [here](https://faker.readthedocs.io/en/master/providers.html).

It scales really nicely, meaning you can generate large quantities of fake data in seconds.

Read the [new Medium article](https://medium.com/snowflake/dc5e65225a13) for further info and examples.

## Contributors

- James Weakley ([Omnata](https://omnata.com))


## Examples

Generate 5000 fake names, in the US English locale:
```
select FAKE('en_US','name',{}) as FAKE_NAME
    from table(generator(rowcount => 5000))
```
![fake names example](/example_names.png "Example")

100 dates between 180 days ago and today::
```
select FAKE('en_US','date_between',{'start_date':'-180d','end_date':'today'})::date as FAKE_DATE
 from table(generator(rowcount => 50));
```
![fake dates example](/example_dates.png "Example")

Generate 100 fake profile attributes (name, job, company), and extract them from the returned variant column:
```
with FAKE_PROFILES as (
    select FAKE('en_AU','profile',{'fields':'name,job,company'}) as FAKE_PROFILE
    from table(generator(rowcount => 100))
    )
select FAKE_PROFILE:company::varchar,FAKE_PROFILE:job::varchar,FAKE_PROFILE:name::varchar
from FAKE_PROFILES
```
![fake profiles example](/example_profile.png "Example")
