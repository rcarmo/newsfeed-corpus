<fetch-table>
    <table class="bordered">
        <thead>
        <tr>
            <th>Time</th>
            <th>URL</th>
            <th>Status</th>
        </tr>
        </thead>

        <tbody>
        <tr each={events}>
            <td>{time}</td>
            <td class="truncate">{url}</td>
            <td>{status}</td>
        </tr>
        </tbody>
    </table>
    <script>
        this.mixin(SharedMixin);
        var self = this;
        self.events = [];

        self.on('mount', function() {
            this.source.addEventListener("fetch_result", function (e) {
                var item = JSON.parse(e.data);
                item.time = new Date().getTime();
                self.events.unshift(item);
                if(self.events.length > 10) {
                    self.events.pop();
                }
                self.update();
            }, false);
        })
    </script>
</fetch-table>