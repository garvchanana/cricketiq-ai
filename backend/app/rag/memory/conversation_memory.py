class ConversationMemory:

    conversations = {}


    @classmethod
    def add_message(
        cls,
        session_id: str,
        role: str,
        content: str
    ):

        if session_id not in cls.conversations:

            cls.conversations[
                session_id
            ] = []

        cls.conversations[
            session_id
        ].append({

            "role": role,

            "content": content
        })


    @classmethod
    def get_history(
        cls,
        session_id: str
    ):

        return cls.conversations.get(
            session_id,
            []
        )