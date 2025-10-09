const winston = require('winston');
const { combine, timestamp, printf, colorize, align } = winston.format;

/** @typedef {{level: string, message: string, timestamp: string, [key: string]: any}} LogMetadata */

/**
 * @param {LogMetadata} param0 
 * @returns {string}
 */
const customFormat = printf((info: { level: string; message: string; timestamp: string;[key: string]: any }) => {
    const { level, message, timestamp, ...metadata } = info;
    let msg = `${timestamp} [${level}] ${message}`;

    if (metadata && Object.keys(metadata).length > 0) {
        msg += ` ${JSON.stringify(metadata)}`;
    }

    return msg;
});

export const logger = winston.createLogger({
    level: 'info',
    format: combine(
        colorize(),
        timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
        align(),
        customFormat
    ),
    transports: [
        new winston.transports.Console()
    ]
});

// During development, log everything
if (process.env.NODE_ENV !== 'production') {
    logger.level = 'debug';
}

export default logger;

