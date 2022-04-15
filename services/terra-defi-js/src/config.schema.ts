import * as Joi from 'joi';

export const configValidationSchema = Joi.object({
    SERVER_PORT_HTTP: Joi.string().default(5020).required(),
    SERVER_PORT_HTTPS: Joi.string().default(5021).required(),
    DB_TYPE: Joi.string().default('postgres').required(),
    DB_HOST: Joi.string().default('localhost').required(),
    DB_PORT: Joi.number().default(5432).required(),
    DB_USERNAME: Joi.string().required(),
    DB_PASSWORD: Joi.string().required(),
    DB_NAME: Joi.string().required(),
    JWT_SECRET: Joi.string().min(1020).required()
});
