<sse-counter>
    <script>
        var self = this;
        this.mixin(SharedMixin);

        self.on('mount', function () {

            e.addEventListener("message", function (e) {
                self.value = e.data;
                console.log(self.value);
                
                self.update();
            }, false);
        })
    </script>
</sse-counter>