/* WetSoil custom Lovelace card. Backend is the source of truth for all settings. */
const LANG = {
  en: {
    title:"WetSoil",select:"Circuit",status:"Status",auto:"Automatic irrigation",
    messages:{"not_checked":"Not checked yet","complete":"Complete","recorder_complete":"Recorder data complete","recorder_incomplete":"Recorder data incomplete","recorder_not_loaded":"Recorder not enabled","recorder_entity_excluded":"Sensor excluded from Recorder","recorder_error":"Failed to retrieve Recorder data","intensity_72h_complete":"72-hour precipitation intensity history complete","intensity_72h_incomplete":"72-hour precipitation intensity history incomplete","intensity_sensor_unavailable":"Precipitation intensity sensor unavailable","sensor_not_configured":"No precipitation sensor selected","weather_unconfigured":"No weather entity selected","weather_updating":"Updating weather","weather_unavailable":"Weather entity unavailable","forecast_incomplete":"Forecast incomplete","forecast_unavailable":"Forecast unavailable","hourly_incomplete":"Hourly forecast incomplete","daily_incomplete":"Daily forecast incomplete","hourly_unavailable":"Hourly forecast unavailable","daily_unavailable":"Daily forecast unavailable","incomplete":"Data incomplete","ready":"Data complete","unavailable":"Unavailable","allowed":"Watering permitted","raining":"Currently raining","rain_3d_limit":"Historical precipitation limit reached","rain_today_limit":"Today's precipitation limit reached","temperature_limit":"Temperature threshold reached","invalid_precipitation":"Invalid precipitation value","invalid_parameters":"Invalid calculation parameters","rain_or_unknown":"Rain or unknown rain status","rain_sources_disagree":"Rain sensor and weather entity disagree","automatic_disabled":"Automatic watering disabled","no_valves":"No valves configured","calendar_excluded":"Day or month excluded","already_running":"Watering already running","already_watered_today":"Already watered automatically today","not_eligible":"Start conditions not met","start_failed":"Start failed","stop_command_failed":"Switch-off command failed","valve_not_off":"Valve already on or unavailable","previous_start_requires_explicit_stop":"Explicitly stop previous start","manual":"Manual","auto":"Automatic","idle":"Idle","stopped":"Stopped","starting":"Starting","watering":"Watering in progress","error":"Error","daily":"Daily forecast","hourly":"Hourly forecast"},
    computed:"Weather calculation",planned:"Scheduled duration",remaining:"Remaining",
    start:"Manual start",stop:"Immediate stop",weather:"Weather",settings:"Settings",
    valves:"Valves",schedule:"Schedule",parameters:"Calculation parameters",
    measured:"Observed rain, last 3 days",forecast:"Forecast rain today",temp:"Max temperature",
    raining:"Currently raining",quality:"Data quality",reason:"Reason",saved:"Settings saved",
    forecastSource:"Forecast source",forecastEntity:"Forecast entity",historyStatus:"History source status",
    error:"Error",save:"Save settings",events:"Recent events",seconds:"seconds",
    weather_entity:"Weather entity",rain_sensor:"Rain binary sensor",
    precipitation_sensor:"Observed precipitation sensor",
    precipitation_sensor_kind:"Precipitation sensor type",
    base_seconds:"Base watering duration (seconds)",
    max_rain_today:"Maximum forecast rain (mm)",
    max_rain_3d:"Maximum 3-day average (mm/day)",
    min_temp:"Lower temperature threshold (°C)",
    max_temp:"Upper temperature threshold (°C)",
    max_runtime:"Maximum safety runtime (seconds)",
    start_mode:"Start mode",time:"Absolute time",chained:"After predecessor",
    predecessor:"Predecessor circuit",start_time:"Start time",weekdays:"Allowed weekdays",
    months:"Allowed months",add:"Add valve",remove:"Remove",none:"None",
    weekdayNames:["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
    monthNames:["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
    history:"Actual precipitation",unavailable:"Unavailable",refresh:"Refresh",
    factor:"Calculation factors",next:"Next start",
    scheduleToday:"Today’s schedule", localTime:"HA local time",
    wateredToday:"Started today",automaticWateredToday:"Automatic run started today",
    lastActualRun:"Last actual start",lastRunKind:"Last start type",
    lastSkip:"Last skipped attempt",lastSkipReason:"Last skip reason",
    resetToday:"Reset today’s run status",
    confirmReset:"Reset today's run markers? This does not switch actuators.",
    yes:"Yes",no:"No",
    scheduleMessages:{
      chained:"After predecessor",month_excluded:"Current month is excluded",
      weekday_excluded:"Today’s weekday is excluded",
      time_nonexistent:"Local time does not exist",
      time_passed:"Today’s scheduled time has passed",
      already_attempted:"Today’s start was already attempted",
      already_watered_today:"An automatic run already started today",
      today_allowed:"Start is permitted today"
    },sensorTotal:"Cumulative total",sensorDaily:"Daily total",sensorIntensity:"Actual precipitation intensity (mm/h)",
    selectRequired:"Select a WetSoil circuit in the card editor before using this card.",
    invalidSelection:"The selected WetSoil circuit no longer exists. Choose a valid circuit in the card editor.",
    after:"After", rainConflict:"Rain sensor and weather report contradictory conditions.",
    errors:{
      cyclic_predecessor:"Circular circuit chaining is not allowed.",
      invalid_predecessor:"Invalid predecessor or more than one successor in the chain.",
      missing_predecessor:"Choose a predecessor before saving.",
      shared_valve:"This valve belongs to another circuit.",
      invalid_temperature_range:"The upper temperature limit must exceed the lower limit.",
      invalid_config:"Invalid configuration."
    }
  },
  de: {
    title:"WetSoil",select:"Bewässerungskreis",status:"Status",auto:"Automatik aktiviert",
    messages:{"not_checked":"Noch nicht geprüft","complete":"Vollständig","recorder_complete":"Recorder-Daten vollständig","recorder_incomplete":"Recorder-Daten unvollständig","recorder_not_loaded":"Recorder nicht aktiviert","recorder_entity_excluded":"Sensor nicht im Recorder enthalten","recorder_error":"Fehler beim Laden der Recorder-Daten","intensity_72h_complete":"72 Stunden Niederschlagsintensität vollständig ausgewertet","intensity_72h_incomplete":"72 Stunden Niederschlagsintensität unvollständig","intensity_sensor_unavailable":"Niederschlagsintensitätssensor nicht verfügbar","sensor_not_configured":"Kein Niederschlagssensor ausgewählt","weather_unconfigured":"Keine Wetter-Entity ausgewählt","weather_updating":"Wetterdaten werden aktualisiert","weather_unavailable":"Wetter-Entity nicht verfügbar","forecast_incomplete":"Wetterprognose unvollständig","forecast_unavailable":"Keine Wetterprognose verfügbar","hourly_incomplete":"Stundenprognose unvollständig","daily_incomplete":"Tagesprognose unvollständig","hourly_unavailable":"Stundenprognose nicht verfügbar","daily_unavailable":"Tagesprognose nicht verfügbar","incomplete":"Daten unvollständig","ready":"Daten vollständig","unavailable":"Nicht verfügbar","allowed":"Bewässerung freigegeben","raining":"Es regnet","rain_3d_limit":"Historischer Niederschlagsgrenzwert erreicht","rain_today_limit":"Heutiger Niederschlagsgrenzwert erreicht","temperature_limit":"Temperaturgrenze erreicht","invalid_precipitation":"Ungültiger Niederschlagswert","invalid_parameters":"Ungültige Berechnungsparameter","rain_or_unknown":"Regen oder unbekannter Regenstatus","rain_sources_disagree":"Regensensor und Wetter-Entity widersprechen sich","automatic_disabled":"Automatik deaktiviert","no_valves":"Keine Ventile konfiguriert","calendar_excluded":"Tag oder Monat nicht freigegeben","already_running":"Bewässerung läuft bereits","already_watered_today":"Heute bereits automatisch bewässert","not_eligible":"Startbedingungen nicht erfüllt","start_failed":"Start fehlgeschlagen","stop_command_failed":"Ausschaltbefehl fehlgeschlagen","valve_not_off":"Ventil ist bereits eingeschaltet oder nicht erreichbar","previous_start_requires_explicit_stop":"Vorherigen Start bitte ausdrücklich stoppen","manual":"Manuell","auto":"Automatisch","idle":"Bereit","stopped":"Gestoppt","starting":"Startet","watering":"Bewässerung läuft","error":"Fehler","daily":"Tagesprognose","hourly":"Stundenprognose"},
    computed:"Wetterabhängig berechnet",planned:"Tatsächlich geplant",remaining:"Restlaufzeit",
    start:"Manueller Start",stop:"Sofort-Stopp",weather:"Wetter",settings:"Einstellungen",
    valves:"Ventile",schedule:"Zeitplanung",parameters:"Berechnungsparameter",
    measured:"Gemessener Regen, letzte 3 Tage",forecast:"Regenprognose heute",temp:"Maximale Temperatur",
    raining:"Aktueller Regen",quality:"Datenqualität",reason:"Sperrgrund",saved:"Einstellungen gespeichert",
    forecastSource:"Prognosequelle",forecastEntity:"Wetter-Entity",historyStatus:"Status der Niederschlagshistorie",
    error:"Fehler",save:"Einstellungen speichern",events:"Letzte Ereignisse",seconds:"Sekunden",
    weather_entity:"Wetter-Entity",rain_sensor:"Regen-Binary-Sensor",
    precipitation_sensor:"Gemessener Niederschlagssensor",
    precipitation_sensor_kind:"Art der Niederschlagsmessung",
    base_seconds:"Basisberegnungszeit (Sekunden)",
    max_rain_today:"Maximale Regenprognose (mm)",
    max_rain_3d:"Maximaler 3-Tage-Durchschnitt (mm/Tag)",
    min_temp:"Untere Temperaturgrenze (°C)",
    max_temp:"Obere Temperaturgrenze (°C)",
    max_runtime:"Maximale Sicherheitslaufzeit (Sekunden)",
    start_mode:"Startmodus",time:"Absolute Uhrzeit",chained:"Nach Vorgänger",
    predecessor:"Vorgängerinstanz",start_time:"Startuhrzeit",weekdays:"Zulässige Wochentage",
    months:"Zulässige Monate",add:"Ventil hinzufügen",remove:"Entfernen",none:"Keiner",
    weekdayNames:["Mo","Di","Mi","Do","Fr","Sa","So"],
    monthNames:["Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"],
    history:"Tatsächlicher Niederschlag",unavailable:"Nicht verfügbar",refresh:"Aktualisieren",
    factor:"Berechnungsfaktoren",next:"Nächster Start",
    scheduleToday:"Zeitplan heute",localTime:"HA-Ortszeit",
    wateredToday:"Heute tatsächlich gestartet",automaticWateredToday:"Automatik heute gestartet",
    lastActualRun:"Letzter tatsächlicher Start",lastRunKind:"Art des letzten Starts",
    lastSkip:"Letzter übersprungener Versuch",lastSkipReason:"Grund für Überspringen",
    resetToday:"Heutigen Laufstatus zurücksetzen",
    confirmReset:"Heutige Laufmarkierungen zurücksetzen? Die Aktoren werden nicht geschaltet.",
    yes:"Ja",no:"Nein",
    scheduleMessages:{
      chained:"Nach Vorgänger",month_excluded:"Monat nicht freigegeben",
      weekday_excluded:"Heutiger Wochentag nicht freigegeben",
      time_nonexistent:"Ortszeit existiert nicht",
      time_passed:"Heutige Startzeit bereits vergangen",
      already_attempted:"Heutiger Startversuch bereits erfolgt",
      already_watered_today:"Automatische Bewässerung heute bereits gestartet",
      today_allowed:"Start heute zulässig"
    },sensorTotal:"Kumulativer Zähler",sensorDaily:"Tagessumme",sensorIntensity:"Niederschlagsintensität (mm/h)",
    selectRequired:"Bitte zuerst im Card-Editor einen WetSoil-Bewässerungskreis auswählen.",
    invalidSelection:"Der ausgewählte Bewässerungskreis existiert nicht mehr. Bitte im Card-Editor neu auswählen.",
    after:"Nach", rainConflict:"Regen-Sensor und Wetter-Entity melden widersprüchliche Zustände.",
    errors:{
      cyclic_predecessor:"Eine Ringverkettung ist nicht erlaubt.",
      invalid_predecessor:"Ungültiger Vorgänger oder mehrere Nachfolger in der Kette.",
      missing_predecessor:"Bitte eine Vorgängerinstanz auswählen.",
      shared_valve:"Das Ventil wird bereits von einem anderen Bewässerungskreis verwendet.",
      invalid_temperature_range:"Die obere Temperaturgrenze muss höher als die untere sein.",
      invalid_config:"Ungültige Konfiguration."
    }
  }
};

const STYLES = [
  ".root{padding:16px}",
  ".heading{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}",
  ".metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:12px 0}",
  ".metric{border:1px solid var(--divider-color);border-radius:9px;padding:9px}",
  ".metric small{display:block;opacity:.75;margin-bottom:5px}",
  ".actions,.horizontal{display:flex;flex-wrap:wrap;align-items:center;gap:10px}",
  "button{font:inherit;cursor:pointer;background:var(--primary-color);color:white;border:0;border-radius:6px;padding:8px 14px}",
  "button:disabled{opacity:.5;cursor:default}",
  ".danger{background:var(--error-color)}",
  "label{display:block;margin:10px 0}",
  "input[type=number],input[type=time],select{box-sizing:border-box;width:100%;background:var(--card-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color);border-radius:6px;padding:8px;font:inherit}",
  "ha-entity-picker{display:block;max-width:100%;margin:6px 0}",
  "details{margin-top:14px}",
  "details details{padding:8px;border-bottom:1px solid var(--divider-color)}",
  ".error{color:var(--error-color)}",
  ".checks{display:flex;flex-wrap:wrap;gap:8px}",
  ".checks label{margin:0;border:1px solid var(--divider-color);border-radius:5px;padding:7px}",
  "summary{cursor:pointer;font-weight:600;margin-bottom:8px}"
].join("");

function elem(tag, text=null, className=null) {
  const node=document.createElement(tag);
  if (text!==null) node.textContent=String(text);
  if (className) node.className=className;
  return node;
}

class WetSoilCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._render();
  }
  set hass(hass) {
    this._hass = hass;
    if (!this._loading && (!this._loaded || (!this._editing && Date.now()-(this._at||0)>10000))) {
      this._refresh();
    }
  }
  getCardSize() { return 8; }
  static getConfigElement() { return document.createElement("wetsoil-card-editor"); }
  static getStubConfig() { return {entry_id:""}; }
  _t(key) {
    const lang=this._hass?.locale?.language?.startsWith("de") ||
      this._hass?.language?.startsWith("de") ? "de" : "en";
    return LANG[lang][key] || key;
  }
  _errorText(error) {
    const raw = typeof error === "string" ? error :
      error?.message || error?.code || error?.error?.message || error?.error?.code || "";
    const reason = String(raw || "unknown_error");
    const key = reason.split(":")[0];
    const lang = this._hass?.locale?.language?.startsWith("de") ||
      this._hass?.language?.startsWith("de") ? "de" : "en";
    return LANG[lang].errors[key] || LANG[lang].messages[key] || (reason === "[object Object]" ?
      LANG[lang].errors.invalid_config : reason.replaceAll("_"," "));
  }
  _humanize(value) {
    if (value === null || value === undefined) return this._t("unavailable");
    if (typeof value !== "string") return value;
    const lang = this._hass?.locale?.language?.startsWith("de") ||
      this._hass?.language?.startsWith("de") ? "de" : "en";
    const messages = LANG[lang].messages;
    // Comma-separated forecast diagnostics should each be translated.
    if (value.includes(",") && value.split(",").every(code=>messages[code])) {
      return value.split(",").map(code=>messages[code]).join("; ");
    }
    const prefix = value.split(":")[0];
    if (messages[prefix] && value.includes(":")) {
      return messages[prefix] + ": " + value.slice(prefix.length+1);
    }
    return messages[value] || value;
  }
  _eventText(event) {
    if (typeof event !== "string") return String(event ?? "");
    const translations = this._hass?.locale?.language?.startsWith("de") ||
      this._hass?.language?.startsWith("de") ? {
       "Automatic watering skipped: ":"Automatischer Start übersprungen: ",
       "Watering started: ":"Bewässerung gestartet: ",
       "WetSoil run stopped: ":"Bewässerung beendet: ",
       "WetSoil run stopped":"Bewässerung beendet",
       "Today's watering markers reset by administrator":"Heutiger Laufstatus zurückgesetzt",
       "Nonexistent local start time: skipped":"Nicht existierende lokale Startzeit übersprungen",
       "Start failed; actuators may remain on. Use explicit Stop or external controls.":"Start fehlgeschlagen; Aktor eventuell eingeschaltet. Bitte ausdrücklich stoppen oder extern bedienen.",
       "Interrupted run not resumed; external shutdown is the user's responsibility":"Unterbrochener Lauf nicht fortgesetzt; externe Abschaltung erforderlich",
       "WetSoil unloaded; actuator state left unchanged. External safety required.":"Integration entladen; Aktor unverändert. Externe Absicherung erforderlich."
      } : {};
    const key=Object.keys(translations).find(k=>event.startsWith(k));
    return key ? translations[key] + (event.slice(key.length).startsWith(": ") ?
      event.slice(key.length) : this._humanize(event.slice(key.length))) : this._humanize(event);
  }
  _scheduleText(code) {
    const lang = this._hass?.locale?.language?.startsWith("de") ||
      this._hass?.language?.startsWith("de") ? "de" : "en";
    return LANG[lang].scheduleMessages[code] || code || this._t("unavailable");
  }
  _formatNextStart(value) {
    if (typeof value !== "string" || !value) return this._t("unavailable");
    if (value.startsWith("after:")) {
      const id = value.substring(6);
      const name = this._circuits?.find(c=>c.entry_id===id)?.name;
      return name ? this._t("after")+" "+name : this._t("unavailable");
    }
    const date = new Date(value);
    if (!Number.isFinite(date.getTime())) return this._t("unavailable");
    const lang = this._hass?.locale?.language || this._hass?.language || "en";
    const timezone = this._hass?.config?.time_zone;
    try {
      return new Intl.DateTimeFormat(lang, {
        day:"2-digit", month:"2-digit", year:"numeric",
        hour:"2-digit",minute:"2-digit",hourCycle:"h23",
        ...(timezone?{timeZone:timezone}:{})
      }).format(date);
    } catch (_) {
      return date.toLocaleString(lang);
    }
  }
  async _refresh() {
    if (!this._hass || this._loading) return;
    this._loading=true;
    try {
      this._circuits=await this._hass.callWS({type:"wetsoil/list"});
      this._loaded=true;
      this._at=Date.now();
    } catch(error) { this._error=this._errorText(error); }
    this._loading=false;
    this._render();
  }
  _current() {
    // Never redirect reads or writes to a different circuit.
    const entryId = this._config?.entry_id;
    if (typeof entryId !== "string" || !entryId) return undefined;
    return this._circuits?.find(c => c.entry_id === entryId);
  }
  async _send(type, extra={}) {
    const circuit=this._current();
    if (!circuit || !this._hass || !this._config?.entry_id) {
      this._error=this._t("selectRequired");
      this._render();
      return;
    }
    try {
      // Prevent extra fields from overriding this card's selected entry.
      await this._hass.callWS({type:"wetsoil/"+type,...extra,entry_id:circuit.entry_id});
      this._error="";
      this._notice=this._t("saved");
    } catch(error) {
      this._notice="";
      this._error=this._errorText(error);
    }
    this._editing=Boolean(this._error && type==="update");
    await this._refresh();
  }
  _metric(host,key,value,unit="") {
    const container=elem("div",null,"metric");
    container.append(elem("small",this._t(key)));
    const decimals = key==="temp" ? 1 : (
      ["forecast","measured"].includes(key) ? 2 : null);
    const text=value===null || value===undefined?this._t("unavailable"):(
      decimals!==null && typeof value==="number" && Number.isFinite(value)
        ? new Intl.NumberFormat(this._hass?.locale?.language||this._hass?.language||"en",
            {minimumFractionDigits:decimals,maximumFractionDigits:decimals}).format(value)
        : String(value));
    container.append(elem("strong",text+((value===null || value===undefined)?"":unit)));
    host.append(container);
  }
  _field(host,key,config,domain) {
    const label=elem("label",this._t(key));
    const picker=elem("ha-entity-picker");
    picker.hass=this._hass;
    picker.value=config[key]||"";
    picker.includeDomains=[domain];
    picker.addEventListener("value-changed",event=>{
      config[key]=event.detail.value||null;
      this._editing=true;
    });
    label.append(picker);
    host.append(label);
  }
  _numeric(host,key,config) {
    const label=elem("label",this._t(key));
    const input=elem("input");
    input.type="number";input.step="any";
    input.value=String(config[key]);
    input.addEventListener("change",()=>{
      config[key]=input.value===""?null:Number(input.value);
      this._editing=true;
    });
    label.append(input);host.append(label);
  }
  _choice(host,key,options,config) {
    const label=elem("label",this._t(key));
    const select=elem("select");
    for(const [value,text] of options) {
      const option=elem("option",text);
      option.value=value;
      option.selected=config[key]===value;
      select.append(option);
    }
    select.addEventListener("change",()=>{
      config[key]=select.value;
      if (key==="start_mode") {
        config.predecessor=null;
        this._editing=true;
      }
    });
    label.append(select);host.append(label);
    return select;
  }
  _checks(host,key,range,config,labels) {
    host.append(elem("p",this._t(key)));
    const row=elem("div",null,"checks");
    for(const number of range) {
      const label=elem("label");
      const input=elem("input");
      input.type="checkbox";
      input.checked=config[key].includes(number);
      input.addEventListener("change",()=>{
        config[key]=Array.from(row.querySelectorAll("input:checked")).map(el=>Number(el.value));
        this._editing=true;
      });
      input.value=String(number);
      label.append(input,document.createTextNode(" "+labels[number-(key==="months"?1:0)]));
      row.append(label);
    }
    host.append(row);
  }
  _render() {
    if (!this._config || !this._hass) return;
    const c=this._current();
    this.replaceChildren();
    const card=elem("ha-card");
    const style=elem("style");style.textContent=STYLES;
    const root=elem("div",null,"root");
    const heading=elem("div",null,"heading");
    heading.append(elem("h2",this._t("title")+(c?" — "+c.name:"")));
    const reload=elem("button",this._t("refresh"));
    reload.onclick=()=>{this._editing=false;this._refresh();};
    heading.append(reload);root.append(heading);
    if (!c) {
      const missing = !this._config?.entry_id;
      root.append(elem("p",this._error||this._t(missing?"selectRequired":"invalidSelection"),"error"));
      card.append(style,root);this.append(card);return;
    }
    const metrics=elem("div",null,"metrics");
    for(const [key,value,unit] of [
      ["status",this._humanize(c.status),""],["computed",c.computed_seconds," s"],
      ["planned",c.planned_seconds," s"],["remaining",Math.round(c.remaining_seconds||0)," s"],
      ["temp",c.temperature," °C"],["forecast",c.rain_today," mm"],
      ["measured",c.rain_3d," mm/day"],["raining",c.raining,""],
      ["quality",this._humanize(c.quality),""],["forecastSource",this._humanize(c.forecast_source),""],
      ["forecastEntity",c.forecast_entity,""],["historyStatus",this._humanize(c.history_status),""],
      ["reason",c.rain_source_disagreement
        ? this._t("rainConflict") : this._humanize(c.reason),""],
      ["next",this._formatNextStart(c.next_start),""],
      ["scheduleToday",this._scheduleText(c.schedule_today),""],
      ["localTime",this._formatNextStart(c.schedule_local_now),""],
      ["wateredToday",c.watered_today,""],
      ["automaticWateredToday",c.automatic_watered_today,""],
      ["lastActualRun",this._formatNextStart(c.last_real_start),""],
      ["lastRunKind",this._humanize(c.last_real_start_kind),""],
      ["lastSkip",this._formatNextStart(c.last_skip_at),""],
      ["lastSkipReason",this._humanize(c.last_skip_reason),""]]) {
        this._metric(metrics,key,value,unit);
      }
    root.append(metrics);
    const active=elem("label");
    const check=elem("input");check.type="checkbox";check.checked=c.config.automatic;
    check.onchange=()=>{
      check.disabled=true;
      this._send("action",{action:check.checked?"enable":"disable"});
    };
    active.append(check,document.createTextNode(" "+this._t("auto")));
    root.append(active);
    const actions=elem("div",null,"actions");
    const start=elem("button",this._t("start"));
    start.onclick=()=>this._send("action",{action:"start"});
    const stop=elem("button",this._t("stop"),"danger");
    stop.onclick=()=>this._send("action",{action:"stop"});
    const reset=elem("button",this._t("resetToday"));
    reset.onclick=()=>{
      if (window.confirm && !window.confirm(this._t("confirmReset"))) return;
      this._send("action",{action:"reset_today"});
    };
    reset.disabled=!!c.running;
    actions.append(start,stop,reset);root.append(actions);
    if(this._notice)root.append(elem("p",this._notice));
    root.append(elem("h4",this._t("events")));
    const history=elem("ul");
    for(const event of (c.events||[]).slice(-8).reverse()) {
      history.append(elem("li",this._eventText(event)));
    }
    root.append(history);
    const details=elem("details");
    details.open=!!this._editing;
    details.ontoggle=()=>{
      this._editing=details.open;
    };
    details.append(elem("summary",this._t("settings")));
    const config=JSON.parse(JSON.stringify(c.config));
    const weather=elem("details");weather.open=true;
    weather.append(elem("summary",this._t("weather")));
    this._field(weather,"weather_entity",config,"weather");
    this._field(weather,"rain_sensor",config,"binary_sensor");
    this._field(weather,"precipitation_sensor",config,"sensor");
    this._choice(weather,"precipitation_sensor_kind",[
      ["total",this._t("sensorTotal")],["daily",this._t("sensorDaily")],
      ["intensity",this._t("sensorIntensity")]],config);
    details.append(weather);
    const valves=elem("details");
    valves.append(elem("summary",this._t("valves")));
    const valveList=elem("div");
    const addValve=(value)=>{
      const row=elem("div",null,"horizontal");
      const picker=elem("ha-entity-picker");
      picker.hass=this._hass;picker.includeDomains=["switch"];picker.value=value||"";
      picker.style.flex="1 1 180px";
      picker.addEventListener("value-changed",()=>{
        row.dataset.value=picker.value;
        this._editing=true;
      });
      row.dataset.value=value||"";
      const remove=elem("button",this._t("remove"));
      remove.onclick=()=>{row.remove();this._editing=true;};
      row.append(picker,remove);valveList.append(row);
    };
    config.valves.forEach(addValve);
    const add=elem("button",this._t("add"));
    add.onclick=()=>{addValve("");this._editing=true;};
    valves.append(valveList,add);details.append(valves);
    const params=elem("details");
    params.append(elem("summary",this._t("parameters")));
    for(const key of ["base_seconds","max_rain_today","max_rain_3d",
                       "min_temp","max_temp","max_runtime"]) this._numeric(params,key,config);
    details.append(params);
    const schedule=elem("details");
    schedule.append(elem("summary",this._t("schedule")));
    this._checks(schedule,"weekdays",[0,1,2,3,4,5,6],config,this._t("weekdayNames"));
    this._checks(schedule,"months",[1,2,3,4,5,6,7,8,9,10,11,12],config,this._t("monthNames"));
    const modeSelect=this._choice(schedule,"start_mode",[
      ["time",this._t("time")],["chained",this._t("chained")]],config);
    const timeLabel=elem("label",this._t("start_time"));
    const timeInput=elem("input");timeInput.type="time";timeInput.value=config.start_time;
    timeInput.onchange=()=>{config.start_time=timeInput.value;this._editing=true;};
    timeLabel.append(timeInput);
    const predecessorLabel=elem("label",this._t("predecessor"));
    const predecessor=elem("select");
    for (const [id,name] of [
      ["",this._t("none")],
      ...(this._circuits||[]).filter(x=>x.entry_id!==c.entry_id)
        .map(x=>[x.entry_id,x.name])]) {
      const option=elem("option",name);
      option.value=id;option.selected=(config.predecessor||"")===id;
      predecessor.append(option);
    }
    predecessor.onchange=()=>{config.predecessor=predecessor.value||null;this._editing=true;};
    predecessorLabel.append(predecessor);
    const showMode=()=>{
      timeLabel.hidden=modeSelect.value!=="time";
      predecessorLabel.hidden=modeSelect.value!=="chained";
    };
    modeSelect.addEventListener("change",()=>{
      config.start_mode=modeSelect.value;
      if(config.start_mode==="time")config.predecessor=null;
      showMode();
      this._editing=true;
    });
    schedule.append(timeLabel,predecessorLabel);showMode();
    details.append(schedule);
    const save=elem("button",this._t("save"));
    save.onclick=()=>{
      config.valves=Array.from(valveList.children).map(x=>x.dataset.value).filter(Boolean);
      if (config.start_mode==="chained") config.predecessor=predecessor.value||null;
      else config.predecessor=null;
      this._send("update",{config});
    };
    details.append(save);
    if (this._error) details.append(elem("p",this._error,"error"));
    root.append(details);
    card.append(style,root);
    this.append(card);
  }
}

class WetSoilCardEditor extends HTMLElement {
  setConfig(config) {this._config=config||{};this._render();}
  set hass(hass) {this._hass=hass;this._render();}
  async _render() {
    if (!this._hass || !this._config || this._busy) return;
    this._busy=true;
    try {
      const circuits=await this._hass.callWS({type:"wetsoil/list"});
      this.replaceChildren();
      const label=elem("label","WetSoil circuit / Bewässerungskreis");
      const selector=elem("select");
      selector.required=true;
      const placeholder=elem("option",this._hass.language?.startsWith("de")
        ?"Bitte Bewässerungskreis auswählen"
        :"Select a circuit");
      placeholder.value="";
      placeholder.disabled=true;
      placeholder.selected=!circuits.some(c=>c.entry_id===this._config.entry_id);
      selector.append(placeholder);
      for(const circuit of circuits) {
        const option=elem("option",circuit.name);
        option.value=circuit.entry_id;
        option.selected=circuit.entry_id===this._config.entry_id;
        selector.append(option);
      }
      selector.onchange=()=>{
        if (!selector.value || !circuits.some(c=>c.entry_id===selector.value)) return;
        this._config={...this._config,entry_id:selector.value};
        this.dispatchEvent(new CustomEvent("config-changed",{
          detail:{config:this._config},bubbles:true,composed:true
        }));
      };
      label.append(selector);this.append(label);
    } catch(err){this.textContent=String(err);}
    finally{this._busy=false;}
  }
}
customElements.define("wetsoil-card", WetSoilCard);
customElements.define("wetsoil-card-editor", WetSoilCardEditor);
window.customCards=window.customCards||[];
window.customCards.push({
  type:"wetsoil-card",name:"WetSoil",
  description:"Weather-aware irrigation circuits and configuration"
});
