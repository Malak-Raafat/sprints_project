class MessageBus:
    def __init__(self):
        self.state = {}

    def publish(self, topic, data):
        print(f"[BUS] Published: {topic}")
        self.state[topic] = data

    def consume(self, topic):
        print(f"[BUS] Consumed: {topic}")
        return self.state.get(topic)


bus = MessageBus()
