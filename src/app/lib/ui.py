class ConsoleUI:
    def __init__(self):
        pass

    def get_int(self, prompt, default):
        return self._default_if_none(
            self._prompt_for_int(prompt),
            default
        )

    def get_string(self, prompt):
        return self._prompt_user(prompt)

    def get_int_from_options(self, message, options):
        user_selection = None
        while user_selection is None:
            user_selection = self._get_int_from_options(message, options)
        return user_selection

    def tell_user(self, message):
        print(message)

    def _get_int_from_options(self, message, options):
        criteria = lambda int_: int_ in options
        return self._get_int_if_meets_criteria(message, criteria)

    def get_int_from_range(self, message, default, min_, max_):
        criteria = lambda int_: int_ >= min_ and int_ <= max_
        selected_int = self._get_int_if_meets_criteria(message, criteria)
        return self._default_if_none(selected_int, default)

    def get_yes_or_no(self, prompt, default):
        return self._default_if_none(
            self._parse_yes_or_no(self._prompt_user(prompt)),
            default
        )

    def _get_int_if_meets_criteria(self, message, meets_criteria):
        selection = self._prompt_user(message)
        selection_int = self._parse_int(selection)
        if selection_int is not None and meets_criteria(selection_int):
            return selection_int
        return None

    def _parse_yes_or_no(self, input_str):
        answer = input_str.strip().lower()
        if answer == "y":
            return True
        elif answer == "n":
            return False
        else:
            return None

    def _default_if_none(self, val, default):
        return default if val is None else val

    def _prompt_for_int(self, prompt):
        return self._parse_int(self._prompt_user(prompt))

    def _prompt_user(self, msg):
        return input(f"\n> {msg}\n")

    def _parse_int(self, input_str):
        try:
            return int(input_str.strip())
        except ValueError:
            return None