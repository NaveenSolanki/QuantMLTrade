import datetime


class get_closest_expiry():
    def get_option_contract_name(self, script_name, expiry_date, strike_price, option_type):
        year_last_two_digits = str(expiry_date.year)[-2:]
        # month = str(expiry_date.month).zfill(2)  # Pad single digits with zero
        month = str(expiry_date.month)  # without padding
        day = str(expiry_date.day).zfill(2)  # Pad single digits with zero

        contract_name = f"{script_name}{year_last_two_digits}{month}{day}{strike_price}{option_type}"
        return contract_name

    def get_last_thursday(self, year, month):
        last_day_of_month = datetime.date(year, month, 1) + datetime.timedelta(days=32)
        last_day_of_month = datetime.date(last_day_of_month.year, last_day_of_month.month, 1) - datetime.timedelta(
            days=1)
        while last_day_of_month.weekday() != 3:  # Thursday is weekday 3
            last_day_of_month -= datetime.timedelta(days=1)
        return last_day_of_month

    def get_next_closest_weekly_expiry(self, input_date):

        # get only date from input date
        input_date = input_date.date()

        target_weekday = 3  # Thursday is weekday 3
        days_ahead = (target_weekday - input_date.weekday()) % 7
        next_closest_thursday = input_date + datetime.timedelta(days=days_ahead)

        # Check if the next_closest_thursday is the last Thursday of the month
        while next_closest_thursday == self.get_last_thursday(next_closest_thursday.year, next_closest_thursday.month):
            next_closest_thursday += datetime.timedelta(days=7)

        return next_closest_thursday


# Example usage
if __name__ == '__main__':
    given_date = datetime.date(2022, 7, 22)  # July 15, 2023
    given_date = datetime.datetime(2022, 7, 22, 9, 30, 0)

    expiry_name_object = get_closest_expiry()
    next_closest_thursday = expiry_name_object.get_next_closest_weekly_expiry(given_date)
    print(next_closest_thursday)

    script_name = "BANKNIFTY"
    strike_price = 35000  # You may set the specific strike price if needed
    option_type = "CE"  # You may set "CE" or "PE" if needed

    contract_name = expiry_name_object.get_option_contract_name(script_name, next_closest_thursday, strike_price,
                                                                option_type)

    print("Next Closest Expiring Weekly Contract: ", contract_name)



