// Telegram webhook for Zabbix 7.4, based on the official media type script.
// Source of truth: zabbix_media/telegram/telegram.js (applied with agents/scripts/zbx_mediatype_update.py).
// Changes against the official script are marked with "CUSTOM":
//   - HTML parse mode: macro values are escaped and only Telegram tags from the templates are kept.
//   - {SEV.EMOJI} in templates is replaced by an emoji for severity / recovery / update.
//   - "<b>Label:</b>" lines with an empty, *UNKNOWN* or unresolved {MACRO} value are removed.
//   - Text longer than the Telegram limit (4096 characters) is truncated.
const CLogger = function(serviceName) {
	this.serviceName = serviceName;
	this.INFO = 4
	this.WARN = 3
	this.ERROR = 2
	this.log = function(level, msg) {
		Zabbix.log(level, '[' + this.serviceName + '] ' + msg);
	}
}

const CTlsConfig = function (raw_value) {
	raw_value = String(raw_value).trim().toLowerCase();

	if (['none', 'peer', 'full'].indexOf(raw_value) === -1) {
		raw_value = 'full';
	}

	this.options = {
		SSLVerifyPeer: (raw_value === 'peer' || raw_value === 'full'),
		SSLVerifyHost: (raw_value === 'full')
	};

	this.enabled = (raw_value !== 'none');

	this.checkURL = function (url) {
		if (this.enabled && !/^https:\/\//i.test(url)) {
			throw 'TLS certificate verification is enabled by {$' + 'HTTP.TLS.VERIFY}, but the URL uses plain HTTP: ' + url +
			'. Use an "https://" URL, or set {$' + 'HTTP.TLS.VERIFY} to `none` to disable verification.';
		}

		return url;
	};
}


const CWebhook = function(value) {
	try {
		params = JSON.parse(value);

		if (['0', '1', '2', '3', '4'].indexOf(params.event_source) === -1) {
			throw 'Incorrect "event_source" parameter given: ' + params.event_source + '.\nMust be 0-4.';
		}

		if (['0', '3', '4'].indexOf(params.event_source) !== -1 && ['0', '1'].indexOf(params.event_value) === -1) {
			throw 'Incorrect "event_value" parameter given: ' + params.event_value + '.\nMust be 0 or 1.';
		}

		if (['0', '3', '4'].indexOf(params.event_source) !== -1) {
			if (params.event_source === '1' && ['0', '1', '2', '3'].indexOf(params.event_value) === -1) {
				throw 'Incorrect "event_value" parameter given: ' + params.event_value + '.\nMust be 0-3.';
			}

			if (params.event_source === '0' && ['0', '1'].indexOf(params.event_update_status) === -1) {
				throw 'Incorrect "event_update_status" parameter given: ' + params.event_update_status + '.\nMust be 0 or 1.';
			}

			if (params.event_source === '4') {
				if (['0', '1', '2', '3', '4', '5'].indexOf(params.event_update_nseverity) !== -1 && params.event_update_nseverity != params.event_nseverity) {
					params.event_nseverity = params.event_update_nseverity;
					params.event_severity = params.event_update_severity;
					params.event_update_status = '1';
				}
			}
		}

		this.runCallback = function(name, params) {
			if (typeof this[name] === 'function') {
				return this[name].apply(this, [params]);
			}
		}

		this.handleEvent = function(source, event) {
			const alert = { source: source, event: event };
			return [
				this.runCallback('on' + source + event, alert),
				this.runCallback('on' + event, alert),
				this.runCallback('onEvent', alert)
			];
		}

		this.handleEventless = function(source) {
			const alert = { source: source, event: null };
			return [
				this.runCallback('on' + source, alert),
				this.runCallback('onEvent', alert)
			];
		}

		this.run = function() {
			var results = [];
			if (typeof this.httpProxy === 'string' && this.httpProxy.trim() !== '') {
				this.request.setProxy(this.httpProxy);
			}
			const types = { '0': 'Trigger', '1': 'Discovery', '2': 'Autoreg', '3': 'Internal', '4': 'Service' };

			if (['0', '3', '4'].indexOf(this.params.event_source) !== -1) {
				var event = (this.params.event_update_status === '1')
					? 'Update'
					: ((this.params.event_value === '1') ? 'Problem' : 'Resolve');

				results = this.handleEvent(types[this.params.event_source], event);
			}
			else if (typeof types[this.params.event_source] !== 'undefined') {
				results = this.handleEventless(types[this.params.event_source]);
			}
			else {
				throw 'Unexpected "event_source": ' + this.params.event_source;
			}

			for (idx in results) {
				if (typeof results[idx] !== 'undefined') {
					return JSON.stringify(results[idx]);
				}
			}
		}
		this.tlsConfig = new CTlsConfig(params.tls_verify);
		this.httpProxy = params.http_proxy;
		this.params = params;
		this.runCallback('onCheckParams', {});
	} catch (error) {
		throw 'Webhook processing failed: ' + error;
	}
}

const CParamValidator = {

	isType: function(value, type) {
		if (type === 'array') {
			return Array.isArray(value);
		}
		if (type === 'integer') {
			return CParamValidator.isInteger(value);
		}
		if (type === 'float') {
			return CParamValidator.isFloat(value);
		}

		return (typeof value === type);
	},

	isInteger: function(value) {
		if (!CParamValidator.ifMatch(value, /^-?\d+$/)) {
			return false;
		}

		return !isNaN(parseInt(value));
	},

	isFloat: function(value) {
		if (!CParamValidator.ifMatch(value, /^-?\d+\.\d+$/)) {
			return false;
		}

		return !isNaN(parseFloat(value));
	},

	isDefined: function(value) {
		return !CParamValidator.isType(value, 'undefined');
	},

	isEmpty: function(value) {
		if (!CParamValidator.isType(value, 'string')) {
			throw 'Value "' + value + '" must be a string to be checked for emptiness.';
		}

		return (value.trim() === '');
	},

	isMacroSet: function(value, macro) {
		if (CParamValidator.isDefined(macro)) {
			return !(CParamValidator.ifMatch(value, '^\{' + macro + '\}$'))
		}

		return !(CParamValidator.ifMatch(value, '^\{[$#]{0,1}[A-Z_\.]+[\:]{0,1}["]{0,1}.*["]{0,1}\}$') || value === '*UNKNOWN*')
	},

	withinRange: function(value, min, max) {
		if (!CParamValidator.isType(value, 'number')) {
			throw 'Value "' + value + '" must be a number to be checked for range.';
		}
		if (value < ((CParamValidator.isDefined(min)) ? min : value)
			|| value > ((CParamValidator.isDefined(max)) ? max : value)) {
			return false;
		}

		return true;
	},

	inArray: function(value, array) {
		if (!CParamValidator.isType(array, 'array')) {
			throw 'The array must be an array to check the value for existing in it.';
		}

		return (array.indexOf((typeof value === 'string') ? value.toLowerCase() : value) !== -1);
	},

	ifMatch: function(value, regex) {
		return (new RegExp(regex)).test(value);
	},

	match: function(value, regex) {
		if (!CParamValidator.isType(value, 'string')) {
			throw 'Value "' + value + '" must be a string to be matched with the regular expression.';
		}

		return value.match(new RegExp(regex));
	},

	checkURL: function(value) {
		if (CParamValidator.isEmpty(value)) {
			throw 'URL value "' + value + '" must be a non-empty string.';
		}
		if (!CParamValidator.ifMatch(value, '^(http|https):\/\/.+')) {
			throw 'URL value "' + value + '" must contain a schema.';
		}

		return value.endsWith('/') ? value.slice(0, -1) : value;
	},

	check: function(key, rule, params) {
		if (!CParamValidator.isDefined(rule.type)) {
			throw 'Mandatory attribute "type" has not been defined for parameter "' + key + '".';
		}
		if (!CParamValidator.isDefined(params[key])) {
			throw 'Checked parameter "' + key + '" was not found in the list of input parameters.';
		}
		var value = params[key],
			error_message = null;
		switch (rule.type) {
			case 'string':
				if (!CParamValidator.isType(value, 'string')) {
					throw 'Value "' + key + '" must be a string.';
				}
				if (CParamValidator.isEmpty(value)) {
					error_message = 'Value "' + key + '" must be a non-empty string';
					break;
				}
				if (CParamValidator.isDefined(rule.len) && value.length < rule.len) {
					error_message = 'Value "' + key + '" must be a string with a length > ' + rule.len;
				}
				if (CParamValidator.isDefined(rule.regex) && !CParamValidator.ifMatch(value, rule.regex)) {
					error_message = 'Value "' + key + '" must match the regular expression "' + rule.regex + '"';
				}
				if (CParamValidator.isDefined(rule.url) && rule.url === true) {
					value = CParamValidator.checkURL(value);
				}
				break;
			case 'integer':
				if (!CParamValidator.isInteger(value)) {
					error_message = 'Value "' + key + '" must be an integer';
					break;
				}
				value = parseInt(value);
				break;
			case 'float':
				if (!CParamValidator.isFloat(value)) {
					error_message = 'Value "' + key + '" must be a floating-point number';
					break;
				}
				value = parseFloat(value);
				break;
			case 'boolean':
				if (CParamValidator.inArray(value, ['1', 'true', 'yes', 'on'])) {
					value = true;
				}
				else if (CParamValidator.inArray(value, ['0', 'false', 'no', 'off'])) {
					value = false;
				}
				else {
					error_message = 'Value "' + key + '" must be a boolean-like.';
				}
				break;
			case 'array':
				try {
					value = JSON.parse(value);
				} catch (error) {
					throw 'Value "' + key + '" contains invalid JSON.';
				}
				if (!CParamValidator.isType(value, 'array')) {
					error_message = 'Value "' + key + '" must be an array.';
				}
				if (CParamValidator.isDefined(rule.tags) && rule.tags === true) {
					value = value.reduce(function(acc, obj) {
						acc[obj.tag] = obj.value || null;
						return acc;
					}, {});
				}
				break;
			case 'object':
				value = JSON.parse(value);
				if (!CParamValidator.isType(value, 'object')) {
					error_message = 'Value "' + key + '" must be an object.';
				}
				break;
			default:
				throw 'Unexpected attribute type "' + rule.type + '" for value "' + key + '". Available: ' +
				['integer', 'float', 'string', 'boolean', 'array', 'object'].join(', ');
		}
		params[key] = value;
		if (CParamValidator.inArray(rule.type, ['integer', 'float']) && error_message === null && (CParamValidator.isDefined(rule.min)
			|| CParamValidator.isDefined(rule.max)) && !CParamValidator.withinRange(value, rule.min, rule.max)) {
			error_message = 'Value "' + key + '" must be a number ' + ((CParamValidator.isDefined(rule.min) && CParamValidator.isDefined(rule.max))
				? (rule.min + '..' + rule.max) : ((CParamValidator.isDefined(rule.min)) ? '>' + rule.min : '<' + rule.max));
		}
		else if (CParamValidator.isDefined(rule.array) && !CParamValidator.inArray(value, rule.array)) {
			error_message = 'Value "' + key + '" must be in the array ' + JSON.stringify(rule.array);
		}
		else if (CParamValidator.isDefined(rule.macro) && !CParamValidator.isMacroSet(value.toString(), rule.macro)) {
			error_message = 'The macro ' + ((CParamValidator.isDefined(rule.macro)) ? '{' + rule.macro + '} ' : ' ') + 'is not set';
		}
		if (error_message !== null) {
			if (CParamValidator.isDefined(rule.default) && CParamValidator.isType(rule.default, rule.type)) {
				params[key] = rule.default;
			}
			else {
				Zabbix.log(4, 'Default value for "' + key + '" must be a ' + rule.type + '. Skipped.');
				throw 'Incorrect value for variable "' + key + '". ' + error_message;
			}
		}

		return this;
	},

	validate: function(rules, params) {
		if (!CParamValidator.isType(params, 'object') || CParamValidator.isType(params, 'array')) {
			throw 'Incorrect parameters value. The value must be an object.';
		}
		for (var key in rules) {
			CParamValidator.check(key, rules[key], params);
		}
	}
}

const CHttpRequest = function (logger, tls_config) {
	if (typeof tls_config === 'object' && tls_config !== null) {
		this.tls_config = tls_config;
	}
	else {
		this.tls_config = new CTlsConfig('full');
	}

	this.request = new HttpRequest(this.tls_config.options);

	if (typeof logger !== 'object' || logger === null) {
		this.logger = Zabbix;
	}
	else {
		this.logger = logger;
	}

	this.clearHeader = function () {
		this.request.clearHeader();
	}

	this.addHeaders = function (value) {
		var headers = [];

		if (typeof value === 'object' && value !== null) {
			if (!Array.isArray(value)) {
				Object.keys(value).forEach(function (key) {
					headers.push(key + ': ' + value[key]);
				});
			}
			else {
				headers = value;
			}
		}
		else if (typeof value === 'string') {
			value.split('\r\n').forEach(function (header) {
				headers.push(header);
			});
		}

		for (var idx in headers) {
			this.request.addHeader(headers[idx]);
		}
	}

	this.setProxy = function (proxy) {
		this.request.setProxy(proxy);
	}

	this.plainRequest = function (method, url, data) {
		var resp = null;
		if (this.tls_config.enabled) {
			this.tls_config.checkURL(url);
		}
		method = method.toLowerCase();
		this.logger.log(4, 'Sending ' + method + ' request:' + JSON.stringify(data));
		if (['get', 'post', 'put', 'patch', 'delete', 'trace'].indexOf(method) !== -1) {
			resp = this.request[method](url, data);
		}
		else if (['connect', 'head', 'options'].indexOf(method) !== -1) {
			resp = this.request[method](url);
		}
		else {
			throw 'Unexpected method. Method ' + method + ' is not supported.';
		}
		this.logger.log(4, 'Response has been received: ' + resp);

		return resp;
	}

	this.jsonRequest = function (method, url, data) {
		this.addHeaders('Content-Type: application/json');
		var resp = this.plainRequest(method, url, JSON.stringify(data));
		try {
			resp = JSON.parse(resp);
		}
		catch (error) {
			throw 'Failed to parse response: not well-formed JSON was received';
		}

		return resp;
	}

	this.getStatus = function () {
		return this.request.getStatus();
	}
}

var serviceLogName = 'Telegram Webhook',
	Logger = new CLogger(serviceLogName),
	Telegram = CWebhook;

function escapeMarkup(str, mode) {
	switch (mode) {
		case 'markdown':
			return str.replace(/([_*\[`])/g, '\\$&');
		case 'markdownv2':
			return str.replace(/([_*\[\]()~`>#+\-=|{}.!])/g, '\\$&');
		case 'html':
			// CUSTOM (zabbix_media/telegram): escape everything, including macro values such as
			// "<pppoe-...>" or "&", then restore only the Telegram tags written in the templates.
			return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
				.replace(/&lt;(\/?)(b|strong|i|em|u|ins|s|strike|del|code|pre|blockquote)&gt;/g, '<$1$2>')
				.replace(/&lt;a href="(https?:\/\/[^"<>\s]+)"&gt;/g, '<a href="$1">')
				.replace(/&lt;\/a&gt;/g, '</a>');
		default:
			return str;
	}
}

// CUSTOM (zabbix_media/telegram): {SEV.EMOJI} placeholder and empty lines.
function severityEmoji(params) {
	if (params.event_update_status === '1') {
		return '💬';
	}
	if (params.event_value === '0') {
		return '✅';
	}
	// Not classified, Information, Warning, Average, High, Disaster
	return ['⚪', '🔵', '🟡', '🟠', '🔴', '🔥'][parseInt(params.event_nseverity, 10)] || '⚪';
}

function prepareText(text, params) {
	return text.replace(/\{SEV\.EMOJI\}/g, severityEmoji(params))
		.split('\n')
		// Drop "<b>Label:</b>" lines whose value is empty or unresolved (e.g. no operational data,
		// {EVENT.TAGS.uplink} on a host without that tag)
		.filter(function (line) {
			return !/:<\/b>\s*(\*UNKNOWN\*|\{[A-Z0-9_.]+\})?\s*$/.test(line);
		})
		.join('\n');
}

// CUSTOM: Telegram rejects messages over 4096 characters (after entity parsing). Cut the raw text
// with margin and close the message with an ellipsis; tags are not split because they are short.
function limitLength(text) {
	const max = 3900;
	if (text.length <= max) {
		return text;
	}
	var cut = text.substring(0, max);
	cut = cut.substring(0, Math.max(cut.lastIndexOf('\n'), max - 200));
	return cut + '\n…';
}

Telegram.prototype.getMessageID = function (chat_id, message_thread_id) {
	const tag_key = '__telegram_msg_id_' + chat_id + (message_thread_id ? '_' + message_thread_id : '');
	if (CParamValidator.isDefined(this.params.event_tags[tag_key])) {
		return this.params.event_tags[tag_key];
	}
	return null;
}

Telegram.prototype.onCheckParams = function () {
	CParamValidator.validate(
		{
			api_token: {type: 'string'},
			api_chat_id: {type: 'string'},
			alert_message: {type: 'string'}
		},
		this.params
	);

	if (CParamValidator.inArray(this.params.event_source, ['0', '3', '4'])) {
		CParamValidator.validate({
			event_tags: {type: 'array', macro: 'EVENT.TAGSJSON', tags: true, default: {}}
		}, this.params);
	}

	this.params.url = 'https://api.telegram.org/bot';
	this.data = {
		disable_web_page_preview: true,
		disable_notification: false
	};
	const match = this.params.api_chat_id.match(/^(-?\d+|@[a-zA-Z0-9_]+)(?::(\d+))?$/);
	if (!match) {
		throw 'Invalid format for api_chat_id: "' + this.params.api_chat_id + '". Must be a numeric group ID or @GroupName, optionally followed by :message_thread_id.';
	}
	this.data['chat_id'] = match[1];
	if (CParamValidator.isDefined(match[2])) {
		this.data['message_thread_id'] = match[2];
	}
	this.data['text'] = ((this.params.alert_subject !== '') ? this.params.alert_subject + '\n' : '') + this.params.alert_message;
	this.data['text'] = limitLength(prepareText(this.data['text'], this.params)); // CUSTOM
	if (['markdown', 'html', 'markdownv2'].indexOf(this.params.api_parse_mode.toLowerCase()) !== -1) {
		this.data['parse_mode'] = this.params.api_parse_mode.toLowerCase();
		this.data['text'] = escapeMarkup(this.data['text'], this.data['parse_mode']);
	}
	const reply_to_message_id = this.getMessageID(this.data['chat_id'], this.data['message_thread_id']);
	if (reply_to_message_id !== null) {
		this.data['reply_to_message_id'] = reply_to_message_id;
	}
	this.result = {tags: {}};
};

Telegram.prototype.onEvent = function (alert) {
	Logger.log(Logger.INFO, 'Source: ' + alert.source + '; Event: ' + alert.event);
	Logger.log(Logger.INFO, 'URL: ' + this.params.url.replace(this.params.api_token, '<TOKEN>'));
	var response = this.request.jsonRequest('POST', this.params.url + this.params.api_token + '/sendMessage', this.data);

	if (this.request.getStatus() !== 200 || !CParamValidator.isType(response.ok, 'boolean') || response.ok !== true) {
		Logger.log(Logger.INFO, 'HTTP code: ' + this.request.getStatus());
		if (CParamValidator.isType(response.description, 'string')) {
			throw response.description;
		}
		else {
			throw 'Unknown error. Check debug log for more information.';
		}
	}

	if (CParamValidator.isDefined(response.result.message_id) && this.getMessageID(this.data['chat_id'], this.data['message_thread_id']) === null) {
		this.result.tags['__telegram_msg_id_' + this.data['chat_id'] + (this.data['message_thread_id'] ? '_' + this.data['message_thread_id'] : '')] = response.result.message_id;
	}

	return this.result;
};

try {
	var hook = new Telegram(value);
	hook.request = new CHttpRequest(Logger, hook.tlsConfig);
	return hook.run();
}
catch (error) {
	Logger.log(Logger.WARN, 'notification failed: ' + error);
	throw 'Sending failed: ' + error;
}
