/* WetSoil initial card. No hardware commands are emitted. */
class WetSoilCard extends HTMLElement {
  setConfig(value) { this.config = value || {}; this.render(); }
  set hass(value) {
    this._hass = value;
    if (!this._loading && !this._loaded) this.refresh();
  }
  getCardSize() { return 3; }
  static getConfigElement() { return document.createElement("wetsoil-card-editor"); }
  static getStubConfig() { return {}; }
  async refresh() {
    this._loading = true;
    try {
      this._circuits = await this._hass.callWS({type:"wetsoil/list"});
      this._loaded = true;
    } catch (error) { this._error = String(error); }
    this._loading = false;
    this.render();
  }
  render() {
    if (!this.config || !this._hass) return;
    const c = this._circuits?.find(x=>x.entry_id===this.config.entry_id) || this._circuits?.[0];
    const de = this._hass.language?.startsWith("de");
    const title = de ? "Bewässerungssteuerung noch nicht verfügbar" : "Irrigation control not yet available";
    this.innerHTML = "";
    const card = document.createElement("ha-card");
    const content = document.createElement("div");
    content.style.padding = "16px";
    const heading = document.createElement("h2");
    heading.textContent = "WetSoil" + (c ? " — " + c.name : "");
    const state = document.createElement("p");
    state.textContent = this._error || title;
    const info = document.createElement("p");
    info.textContent = de ? "Automatische und manuelle Ventilsteuerung sind sicherheitshalber gesperrt." :
      "Automatic and manual valve control are disabled for safety.";
    content.append(heading,state,info);
    card.append(content);
    this.append(card);
  }
}
class WetSoilCardEditor extends HTMLElement {
  setConfig(value) { this.config = value || {}; this.render(); }
  set hass(value) { this._hass = value; this.render(); }
  async render() {
    if (!this._hass || !this.config) return;
    let circuits = [];
    try { circuits = await this._hass.callWS({type:"wetsoil/list"}); }
    catch (e) { this.textContent = String(e); return; }
    this.replaceChildren();
    const select = document.createElement("select");
    for(const c of circuits) {
      const option = document.createElement("option");
      option.value = c.entry_id;
      option.textContent = c.name;
      option.selected = c.entry_id === this.config.entry_id;
      select.append(option);
    }
    select.addEventListener("change", ()=>{
      this.config = {...this.config, entry_id:select.value};
      this.dispatchEvent(new CustomEvent("config-changed",{
        detail:{config:this.config},bubbles:true,composed:true
      }));
    });
    this.append(select);
  }
}
customElements.define("wetsoil-card", WetSoilCard);
customElements.define("wetsoil-card-editor", WetSoilCardEditor);
window.customCards = window.customCards || [];
window.customCards.push({type:"wetsoil-card",name:"WetSoil",description:"Irrigation (development preview)"});
