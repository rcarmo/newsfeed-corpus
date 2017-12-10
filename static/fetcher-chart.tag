<fetcher-chart>
    <div class="container">
        <div class="row">
            <div id="donut{this.UID}" class="col ct-chart"></div>
        </div>
    </div>
        
    <script>
        var self = this;
        self.mixin(SharedMixin);
        self.total = 0;
        self.chart = {
            series: [],
            labels: [],
            colors: []
        }

        function label(value) {
            if(value==='None') return ["Pending", "#9e9e9e"];
            if(value==0) return ["Unreachable", "#d50000"];
            if(value < 300) return ["Fetched", "#4caf50"];
            if(value < 400) return ["Redirected", "#81c784"];
            if(value < 500) return ["Inacessible", "#ff9800"];
            return ["Error", "#ff6d00"]
        }

        self.transform = function(data) {
            console.log(data);
            self.total = data.total;
            Object.keys(data.status).forEach(function(key) {
                var l = label(key);
                self.chart.colors.unshift(l[1])
                self.chart.labels.unshift(l[0])
                self.chart.series.unshift(data.status[key]);
            });
            console.log(self.chart);
            self.update();
            var chart = new Chartist.Pie('#donut' + self.UID, self.chart, {
                donut: true,
                donutWidth: 20,
                donutSolid: true,
                startAngle: 270,
                plugins: [
                    Chartist.plugins.legend(),
                    Chartist.plugins.fillDonut({
                        items: [{
                            content: '<span class="card-title">' + self.total + '</span>'
                        }]
                    })
                ]
            });
            chart.on('draw', function (data) {
                if(data.type === 'slice') {
                    console.log(data);
                    console.log(data.index);
                    data.element.attr({
                        'style': 'fill: ' + self.chart.colors[data.index] + ';'
                    });
                }
            })
        } 

        self.on('mount', function() {
            $.getJSON('/stats/fetcher', self.transform);
            // first grab a snapshot through 

            this.source.addEventListener("fetcher_stats", function (e) {
                self.transform(JSON.parse(e.data))
            }, false);
        })
    </script>
</fetcher-chart>