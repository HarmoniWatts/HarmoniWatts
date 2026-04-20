const moment = require('moment-timezone');

class DateUtils {
  static getDateInTimezone(dateStr, timezone) {
    if (dateStr) {
      return moment.tz(dateStr, timezone).startOf('day');
    }
    return moment.tz(timezone).startOf('day');
  }

  static getCurrentInTimezone(timezone) {
    return moment.tz(timezone);
  }

  static formatDate(date, timezone) {
    return date.clone().tz(timezone).format('YYYY-MM-DD');
  }

  static getDaysDifference(date1, date2, timezone) {
    const d1 = moment.tz(date1, timezone).startOf('day');
    const d2 = moment.tz(date2, timezone).startOf('day');
    return d1.diff(d2, 'days');
  }

  static getCurrentHour(timezone) {
    return moment.tz(timezone).hour();
  }

  static formatISO(date, timezone) {
    return date.clone().tz(timezone).format();
  }
}

module.exports = DateUtils;