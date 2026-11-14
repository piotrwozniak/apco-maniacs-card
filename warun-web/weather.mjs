import {languageFor} from './i18n.mjs?v=26';
export const DEFAULTS = Object.freeze({
  name: 'Faryny', latitude: 53.531944, longitude: 21.385556,
  wind_threshold: 5, precip_threshold: 10, forecast_hours: 40,
  timezone: 'Europe/Warsaw', daylight_only: true, language: 'pl',
});
export function configFor(input = {}) {
  const config = {...DEFAULTS, ...input};
  if(config.entity!=null&&config.entity!==''&&(typeof config.entity!=='string'||!/^sensor\.[a-z0-9_]+$/.test(config.entity)))throw new Error('Invalid APCO Weather entity');
  for (const [key, min, max] of [
    ['latitude', -90, 90], ['longitude', -180, 180],
    ['wind_threshold', 0.5, 30], ['precip_threshold', 0, 100], ['forecast_hours', 4, 72],
  ]) {
    if (typeof config[key] !== 'number' || !Number.isFinite(config[key]) || config[key] < min || config[key] > max)
      throw new Error(`Nieprawidłowa wartość: ${key} (${min}–${max}).`);
  }
  if (!Number.isInteger(config.forecast_hours)) throw new Error('Liczba godzin musi być całkowita.');
  if (typeof config.daylight_only !== 'boolean') throw new Error('Opcja daylight_only musi być wartością true lub false.');
  if (typeof config.name !== 'string' || !config.name.trim() || config.name.length > 80) throw new Error('Podaj nazwę miejsca (do 80 znaków).');
  config.language = languageFor(config.language);
  new Intl.DateTimeFormat('pl-PL', {timeZone: config.timezone});
  return config;
}
export function forecastURL(config) {
  const url = new URL('https://api.open-meteo.com/v1/forecast');
  url.search = new URLSearchParams({
    latitude: config.latitude, longitude: config.longitude,
    current: 'temperature_2m,relative_humidity_2m,cloud_cover,wind_speed_10m,wind_direction_10m,surface_pressure',
    hourly: 'temperature_2m,wind_speed_10m,wind_direction_10m,precipitation_probability',
    daily: 'sunrise,sunset', wind_speed_unit: 'ms', temperature_unit: 'celsius',
    timezone: config.timezone, timeformat: 'unixtime', forecast_days: '5',
  });
  return url;
}
const number = value => typeof value === 'number' && Number.isFinite(value) ? value : null;
export function normalize(data) {
  if (data?.hourly_units?.wind_speed_10m !== 'm/s' || data?.hourly_units?.temperature_2m !== '°C')
    throw new Error('Źródło zwróciło nieoczekiwane jednostki pogody.');
  if (!Array.isArray(data?.hourly?.time) || !Array.isArray(data?.daily?.sunrise) || !Array.isArray(data?.daily?.sunset))
    throw new Error('Źródło nie zwróciło prognozy godzinowej lub godzin słońca.');
  const h = data.hourly;
  const hours = h.time.map((time, i) => ({
    time: number(time) === null ? NaN : time * 1000,
    temperature: number(h.temperature_2m?.[i]), wind: number(h.wind_speed_10m?.[i]),
    direction: number(h.wind_direction_10m?.[i]), precip: number(h.precipitation_probability?.[i]),
  })).filter(hour => Number.isFinite(hour.time)).sort((a, b) => a.time - b.time);
  if (!hours.length) throw new Error('Prognoza godzinowa jest pusta.');
  const c = data.current ?? {};
  return {
    hours,
    current: {time: number(c.time) === null ? NaN : c.time * 1000, temperature: number(c.temperature_2m),
      wind: number(c.wind_speed_10m), direction: number(c.wind_direction_10m),
      humidity: number(c.relative_humidity_2m), cloud: number(c.cloud_cover), pressure: number(c.surface_pressure)},
    days: data.daily.sunrise.map((rise, i) => ({
      rise: number(rise) === null ? NaN : rise * 1000,
      set: number(data.daily.sunset[i]) === null ? NaN : data.daily.sunset[i] * 1000,
    })),
  };
}
export function assessment(hour, config) {
  if (number(hour?.wind) === null || number(hour?.precip) === null || hour.wind < 0 || hour.precip < 0 || hour.precip > 100) return 'unknown';
  return hour.wind < config.wind_threshold && hour.precip < config.precip_threshold ? 'good' : 'bad';
}
export function currentHour(data, now = Date.now()) {
  return data.hours.find(hour => hour.time <= now && now < hour.time + 3600000) ?? null;
}
export function windowsFor(data, config, now = Date.now()) {
  const HOUR = 3600000;
  const current = currentHour(data, now);
  const firstTime = current?.time ?? data.hours.find(hour => hour.time >= now)?.time;
  if (firstTime === undefined) return [];
  const horizon = firstTime + config.forecast_hours * HOUR;
  const ranges = [];
  if (config.daylight_only) {
    for (const day of data.days) {
      if (!Number.isFinite(day.rise) || !Number.isFinite(day.set) || day.set <= now) continue;
      // Forecast timestamps provide the local full-hour grid, also across DST.
      const first = data.hours.find(hour => hour.time >= day.rise && hour.time >= firstTime);
      if (!first || first.time >= day.set) continue;
      const end = Math.min(day.set, horizon);
      if (first.time < end) ranges.push({start: first.time, end, daylight: true});
    }
  } else ranges.push({start: firstTime, end: horizon, daylight: false});
  const dayKey = new Intl.DateTimeFormat('en-CA', {timeZone: config.timezone, year:'numeric', month:'2-digit', day:'2-digit'});
  const runs = [];
  for (const {start, end, daylight} of ranges) {
    const hours = data.hours.filter(hour => hour.time >= start && hour.time < end);
    for (const hour of hours) {
      const status = assessment(hour, config);
      const hourEnd = Math.min(hour.time + HOUR, end);
      const previous = runs.at(-1);
      if (previous && previous.end === hour.time && previous.status === status && previous.daylight === daylight && dayKey.format(previous.start) === dayKey.format(hour.time))
        previous.end = hourEnd;
      else runs.push({start: hour.time, end: hourEnd, daylight, status});
    }
  }
  const windows = [];
  for (const {start, end, daylight} of runs) {
    const hours = data.hours.filter(hour => hour.time >= start && hour.time < end);
    const expectedHours = Math.ceil((end - start) / HOUR);
    if (hours.length !== expectedHours || hours.some((hour, i) => hour.time !== start + i * HOUR)) continue;
    const statuses = hours.map(item => assessment(item, config));
    const status = statuses.includes('bad') ? 'bad' : statuses.includes('unknown') ? 'unknown' : 'good';
    const peakWind = hours.filter(hour => number(hour.wind) !== null).reduce((peak, hour) => !peak || hour.wind > peak.wind ? hour : peak, null);
    const temperatures = hours.map(item => item.temperature).filter(value => value !== null);
    windows.push({start, end, hours, daylight, status,
      count: statuses.filter(status => status === 'good').length,
      min: temperatures.length === hours.length ? Math.min(...temperatures) : null,
      max: temperatures.length === hours.length ? Math.max(...temperatures) : null,
      direction: peakWind?.direction ?? null,
      wind: hours.every(item => item.wind !== null) ? Math.max(...hours.map(item => item.wind)) : null,
      precip: hours.every(item => item.precip !== null) ? Math.max(...hours.map(item => item.precip)) : null,
    });
  }
  return windows;
}
export function direction(degrees) {
  if (number(degrees) === null) return '—';
  return ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW'][Math.round(((degrees % 360) + 360) % 360 / 22.5) % 16];
}
