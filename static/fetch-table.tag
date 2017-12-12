<fetch-table>
    <div id="table{UID}" class="container hide">
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
    <div id="message{UID}" class="container center-align grey-text">
       <i class="material-icons large">info_outline</i><br/>
       Nothing being fetched at the moment
    </div>
    <script>
        this.mixin(SharedMixin);
        var self = this;
        self.events = [];

        self.on('mount', function() {
            this.source.addEventListener("fetch_result", function (e) {
                $('#table' + self.UID).removeClass('hide');
                $('#message' + self.UID).addClass('hide');
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
