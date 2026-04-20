import pkg from 'moment-timezone';
const { tz } = pkg;

class DateUtils {
  static getDateInTimezone(dateStr, timezone) {
    if (dateStr) {
      return tz(dateStr, timezone).startOf('day');
    }
    return tz(timezone).startOf('day');
  }

  static getCurrentInTimezone(timezone) {
    return tz(timezone);
  }

  static formatDate(date, timezone) {
    return date.clone().tz(timezone).format('YYYY-MM-DD');
  }

  static getDaysDifference(date1, date2, timezone) {
    const d1 = tz(date1, timezone).startOf('day');
    const d2 = tz(date2, timezone).startOf('day');
    return d1.diff(d2, 'days');
  }

  static getCurrentHour(timezone) {
    return tz(timezone).hour();
  }

  static formatISO(date, timezone) {
    return date.clone().tz(timezone).format();
  }
}

// Export default (clase completa)
export default DateUtils;

// Export nombrado (funciones individuales)
export const {
  getDateInTimezone,
  getCurrentInTimezone,
  formatDate,
  getDaysDifference,
  getCurrentHour,
  formatISO
} = DateUtils;