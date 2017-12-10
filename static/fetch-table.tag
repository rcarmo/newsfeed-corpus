<fetch-table>
    <div class="container">
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
                <td style="max-width: 50%;" class="truncate">{url}</td>
                <td>{status}</td>
            </tr>
            </tbody>
        </table>
    </div>
    <script>
        this.mixin(SharedMixin);
        var self = this;
        self.events = [];

        self.on('mount', function() {
            this.source.addEventListener("fetch_result", function (e) {
                var item = JSON.parse(e.data);
                item.time = moment().format('HH:mm:ss');
                item.url = url.replace(/^http([s]?)\:\/\//g, '');
                self.events.unshift(item);
                if(self.events.length > 10) {
                    self.events.pop();
                }
                self.update();
            }, false);
        })
    </script>
</fetch-table>