<sse-counter>
    <span>{value}</span>
    <script>
        var self = this;

        self.on('mount', function () {
            var e = new EventSource('/events');
            console.log('loaded');

            e.addEventListener("requests", function (e) {
                self.value = e.data;
                self.update();
                console.log(self.value);
            }, false);
        })
    </script>
</sse-counter>