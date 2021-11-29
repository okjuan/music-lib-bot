QUIT = -1
MIN_OPTIONS_TO_SHOW = 10


class InteractiveOptionPicker:
    def __init__(self, options, pick_handler, ui, get_option_description):
        self.options = options
        self.pick_handler = pick_handler
        self.ui = ui
        self.get_option_description = get_option_description

    def launch_interactive_picker(self):
        while True:
            selection = self.get_selection()
            if selection is QUIT:
                self.ui.tell_user("Quitting...")
                break

            self.pick_handler(self.options[selection])
            if not self.user_wants_to_continue():
                break

    def user_wants_to_continue(self):
        return self.ui.get_yes_or_no(
            f"Pick another option? y or n - default is 'y'",
            True
        )

    def get_selection(self):
        num_options = self.get_num_options_desired()
        min_option, max_option = 0, len(self.options)-1
        message = f"Pick an option!\nEnter a number between {min_option} and {max_option} or enter {QUIT} to quit:"
        self.show_options(self.options[:num_options])
        options = [QUIT, *self._get_range_as_list(len(self.options))]
        return self.ui.get_int_from_options(message, options)

    def get_num_options_desired(self):
        if len(self.options) <= MIN_OPTIONS_TO_SHOW:
            return len(self.options)

        min_option, max_option = 1, len(self.options)
        message = f"How many options do you want to see?\n\t(Enter a number between {min_option} and {max_option})\n"
        return self.ui.get_int_from_range(
            message,
            min(max_option, MIN_OPTIONS_TO_SHOW),
            min_option,
            max_option
        )

    def show_options(self, options):
        self.ui.tell_user("\nHere are your options:")
        for idx, option in enumerate(options):
            description = self.get_option_description(option)
            self.ui.tell_user(f"#{idx}\n\t{description}")

    def _get_range_as_list(self, length):
        return list(range(length))