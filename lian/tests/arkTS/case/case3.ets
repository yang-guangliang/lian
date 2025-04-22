function setActionListener() {
  const a = "setArticle";
  const b = "hidePanel";
  const c = "stateChange";
  const d = "requestMore";

  TextReader.on(a, async (id: string) => { console.info(`setArticle ${id}`) });
  TextReader.on(b, () => { console.info(`onHidePanel`) });
  TextReader.on(c, (state: TextReader.ReadState) => {
    this.onStateChanged(state)
  });
  TextReader.on(d, () => {
    TextReader.loadMore(this.newData, true)
  });
}