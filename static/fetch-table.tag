<fetch-table>
    <div class="container">
        <table class="bordered">
            <tbody>
            <tr each={events}>
                <td>{time}</td>
                <td>{status}</td>
                <td style="max-width: 70%;" class="truncate">{url}</td>
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
                item.time = moment().format('HH:mm');
                item.url = item.url.replace(/^http([s]?)\:\/\//g, '');
                console.log(item.url);
                self.events.unshift(item);
                if(self.events.length > 4) {
                    self.events.pop();
                }
                self.update();
            }, false);
        })
    </script>
</fetch-table>
