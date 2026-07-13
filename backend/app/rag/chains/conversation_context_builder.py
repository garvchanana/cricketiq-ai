class ConversationContextBuilder:

    @staticmethod
    def build_conversation_context(
        history
    ):

        if not history:

            return ""

        formatted_history = []

        for message in history:

            role = message.get(
                "role",
                "user"
            )

            content = message.get(
                "content",
                ""
            )

            formatted_history.append(

                f"""
                {role.upper()}:

                {content}
                """
            )

        return "\n".join(
            formatted_history
        )