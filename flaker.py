import json,datetime,decimal
from faker import Faker

def default_json_transform(obj):
    if isinstance(obj, decimal.Decimal):
        return str(obj)
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()

    raise TypeError

def fake(event, context):
    status_code = 200

    # The return value will contain an array of arrays (one inner array per input row).
    array_of_rows_to_return = [ ]

    # initialise row to this value for reporting errors that occur before the row processing
    row = '(none)'

    try:
        # Convert the input from Snowflake a JSON string into a JSON object.
        payload = json.loads(event["body"])

        # This is basically an array of arrays. The inner array contains the
        # row number, and a value for each parameter passed to the function.
        rows = payload["data"]

        # Initialise the Faker object using the local passed in the first external function parameter
        current_locale = rows[0][1]
        fake = Faker(locale=current_locale)

        # For each input row in the JSON object...
        for row in rows:
            # Update the faker locale only if it's different per row 
            # (much slower, and rare that someone would do this)
            if row[1] != current_locale:
                current_locale = row[1]
                fake = Faker(locale=current_locale)

            # The third parameter is for options being passed to the provider
            if len(row) > 3:
                result = fake.format(row[2],row[3])
            else:
                result = fake.format(row[2])

            row_number = row[0]

            output_value = [result]

            # Put the returned row number and the returned value into an array.
            row_to_return = [row_number, result]

            # ... and add that array to the main array.
            array_of_rows_to_return.append(row_to_return)
        json_compatible_string_to_return = json.dumps({"data" : array_of_rows_to_return}, default=default_json_transform)

    except Exception as err:
        # 400 implies some type of error.
        status_code = 400
        # Tell caller what this function could not handle.
        json_compatible_string_to_return = json.dumps({"data" : row,"error" : str(err)})

    # Return the return value and HTTP status code.
    return {
        'statusCode': status_code,
        'body': json_compatible_string_to_return
    }