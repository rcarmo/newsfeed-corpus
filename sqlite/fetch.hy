(import [lxml [etree]]
        [tinydb [TinyDB]]
        [asyncio [coroutine get-event-loop as-completed Semaphore]]
        [aiohttp [request]]
        [tqdm [tqdm]]
        [aiohttp.connector [TCPConnector]])

(def db (TinyDB "feeds.json"))
(def semaphore (Semaphore 5))


(with-decorator coroutine
  (defn fetch-one [feed]
    (print feed)
    (let [[response (yield-from (apply request ["GET" (str (.get feed "url"))] {"compress" true}))]]
      (yield-from (.text response)))))


(with-decorator coroutine
  (defn print-status [feed]
      (print (yield-from (fetch-one feed)))))


(with-decorator coroutine
  (defn show-progress [jobs]
     (for [j (apply tqdm [(as-completed jobs)] {"total" (len jobs)})]
        (yield-from j))))


(defn feeds-from-opml [filename]
  (let [[tree (.parse etree filename)]
        [feeds (.xpath tree "//outline")]]
    (for [feed feeds]
      (yield {"title"(.get feed "title")
              "url"  (.get feed "xmlUrl")}))))

(defn main []
  (let [[loop (get-event-loop)]
        [pool (TCPConnector)]
        [feeds (feeds-from-opml "feeds.opml")]
        [jobs (list (map print-status feeds))]]
    (.run-until-complete loop (show-progress jobs))))


(main)
