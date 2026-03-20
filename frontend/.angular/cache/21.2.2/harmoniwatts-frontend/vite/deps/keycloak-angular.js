import {
  HTTP_INTERCEPTORS,
  HttpHeaders
} from "./chunk-YBWXTNOH.js";
import {
  CommonModule,
  isPlatformBrowser
} from "./chunk-5WRCSYZD.js";
import "./chunk-GNT2F3TB.js";
import {
  Directive,
  EnvironmentInjector,
  Injectable,
  InjectionToken,
  Input,
  NgModule,
  PLATFORM_ID,
  Subject,
  TemplateRef,
  ViewContainerRef,
  combineLatest,
  computed,
  effect,
  from,
  inject,
  makeEnvironmentProviders,
  map,
  mergeMap,
  of,
  provideAppInitializer,
  runInInjectionContext,
  setClassMetadata,
  signal,
  ɵɵNgOnChangesFeature,
  ɵɵdefineDirective,
  ɵɵdefineInjectable,
  ɵɵdefineInjector,
  ɵɵdefineNgModule
} from "./chunk-25QRLV3Z.js";
import {
  Keycloak
} from "./chunk-IIAGNKPU.js";
import {
  __async,
  __spreadProps,
  __spreadValues
} from "./chunk-TXDUYLVM.js";

// node_modules/keycloak-angular/fesm2022/keycloak-angular.mjs
var KeycloakEventTypeLegacy;
(function(KeycloakEventTypeLegacy2) {
  KeycloakEventTypeLegacy2[KeycloakEventTypeLegacy2["OnAuthError"] = 0] = "OnAuthError";
  KeycloakEventTypeLegacy2[KeycloakEventTypeLegacy2["OnAuthLogout"] = 1] = "OnAuthLogout";
  KeycloakEventTypeLegacy2[KeycloakEventTypeLegacy2["OnAuthRefreshError"] = 2] = "OnAuthRefreshError";
  KeycloakEventTypeLegacy2[KeycloakEventTypeLegacy2["OnAuthRefreshSuccess"] = 3] = "OnAuthRefreshSuccess";
  KeycloakEventTypeLegacy2[KeycloakEventTypeLegacy2["OnAuthSuccess"] = 4] = "OnAuthSuccess";
  KeycloakEventTypeLegacy2[KeycloakEventTypeLegacy2["OnReady"] = 5] = "OnReady";
  KeycloakEventTypeLegacy2[KeycloakEventTypeLegacy2["OnTokenExpired"] = 6] = "OnTokenExpired";
  KeycloakEventTypeLegacy2[KeycloakEventTypeLegacy2["OnActionUpdate"] = 7] = "OnActionUpdate";
})(KeycloakEventTypeLegacy || (KeycloakEventTypeLegacy = {}));
var KeycloakAuthGuard = class {
  constructor(router, keycloakAngular) {
    this.router = router;
    this.keycloakAngular = keycloakAngular;
  }
  /**
   * CanActivate checks if the user is logged in and get the full list of roles (REALM + CLIENT)
   * of the logged user. This values are set to authenticated and roles params.
   *
   * @param route
   * @param state
   */
  canActivate(route, state) {
    return __async(this, null, function* () {
      try {
        this.authenticated = yield this.keycloakAngular.isLoggedIn();
        this.roles = yield this.keycloakAngular.getUserRoles(true);
        return yield this.isAccessAllowed(route, state);
      } catch (error) {
        throw new Error("An error happened during access validation. Details:" + error);
      }
    });
  }
};
var KeycloakService = class _KeycloakService {
  constructor() {
    this._keycloakEvents$ = new Subject();
  }
  /**
   * Binds the keycloak-js events to the keycloakEvents Subject
   * which is a good way to monitor for changes, if needed.
   *
   * The keycloakEvents returns the keycloak-js event type and any
   * argument if the source function provides any.
   */
  bindsKeycloakEvents() {
    this._instance.onAuthError = (errorData) => {
      this._keycloakEvents$.next({
        args: errorData,
        type: KeycloakEventTypeLegacy.OnAuthError
      });
    };
    this._instance.onAuthLogout = () => {
      this._keycloakEvents$.next({
        type: KeycloakEventTypeLegacy.OnAuthLogout
      });
    };
    this._instance.onAuthRefreshSuccess = () => {
      this._keycloakEvents$.next({
        type: KeycloakEventTypeLegacy.OnAuthRefreshSuccess
      });
    };
    this._instance.onAuthRefreshError = () => {
      this._keycloakEvents$.next({
        type: KeycloakEventTypeLegacy.OnAuthRefreshError
      });
    };
    this._instance.onAuthSuccess = () => {
      this._keycloakEvents$.next({
        type: KeycloakEventTypeLegacy.OnAuthSuccess
      });
    };
    this._instance.onTokenExpired = () => {
      this._keycloakEvents$.next({
        type: KeycloakEventTypeLegacy.OnTokenExpired
      });
    };
    this._instance.onActionUpdate = (state) => {
      this._keycloakEvents$.next({
        args: state,
        type: KeycloakEventTypeLegacy.OnActionUpdate
      });
    };
    this._instance.onReady = (authenticated) => {
      this._keycloakEvents$.next({
        args: authenticated,
        type: KeycloakEventTypeLegacy.OnReady
      });
    };
  }
  /**
   * Loads all bearerExcludedUrl content in a uniform type: ExcludedUrl,
   * so it becomes easier to handle.
   *
   * @param bearerExcludedUrls array of strings or ExcludedUrl that includes
   * the url and HttpMethod.
   */
  loadExcludedUrls(bearerExcludedUrls) {
    const excludedUrls = [];
    for (const item of bearerExcludedUrls) {
      let excludedUrl;
      if (typeof item === "string") {
        excludedUrl = {
          urlPattern: new RegExp(item, "i"),
          httpMethods: []
        };
      } else {
        excludedUrl = {
          urlPattern: new RegExp(item.url, "i"),
          httpMethods: item.httpMethods
        };
      }
      excludedUrls.push(excludedUrl);
    }
    return excludedUrls;
  }
  /**
   * Handles the class values initialization.
   *
   * @param options
   */
  initServiceValues({
    enableBearerInterceptor = true,
    loadUserProfileAtStartUp = false,
    bearerExcludedUrls = [],
    authorizationHeaderName = "Authorization",
    bearerPrefix = "Bearer",
    initOptions,
    updateMinValidity = 20,
    shouldAddToken = () => true,
    shouldUpdateToken = () => true
  }) {
    this._enableBearerInterceptor = enableBearerInterceptor;
    this._loadUserProfileAtStartUp = loadUserProfileAtStartUp;
    this._authorizationHeaderName = authorizationHeaderName;
    this._bearerPrefix = bearerPrefix.trim().concat(" ");
    this._excludedUrls = this.loadExcludedUrls(bearerExcludedUrls);
    this._silentRefresh = initOptions ? initOptions.flow === "implicit" : false;
    this._updateMinValidity = updateMinValidity;
    this.shouldAddToken = shouldAddToken;
    this.shouldUpdateToken = shouldUpdateToken;
  }
  /**
   * Keycloak initialization. It should be called to initialize the adapter.
   * Options is an object with 2 main parameters: config and initOptions. The first one
   * will be used to create the Keycloak instance. The second one are options to initialize the
   * keycloak instance.
   *
   * @param options
   * Config: may be a string representing the keycloak URI or an object with the
   * following content:
   * - url: Keycloak json URL
   * - realm: realm name
   * - clientId: client id
   *
   * initOptions:
   * Options to initialize the Keycloak adapter, matches the options as provided by Keycloak itself.
   *
   * enableBearerInterceptor:
   * Flag to indicate if the bearer will added to the authorization header.
   *
   * loadUserProfileInStartUp:
   * Indicates that the user profile should be loaded at the keycloak initialization,
   * just after the login.
   *
   * bearerExcludedUrls:
   * String Array to exclude the urls that should not have the Authorization Header automatically
   * added.
   *
   * authorizationHeaderName:
   * This value will be used as the Authorization Http Header name.
   *
   * bearerPrefix:
   * This value will be included in the Authorization Http Header param.
   *
   * tokenUpdateExcludedHeaders:
   * Array of Http Header key/value maps that should not trigger the token to be updated.
   *
   * updateMinValidity:
   * This value determines if the token will be refreshed based on its expiration time.
   *
   * @returns
   * A Promise with a boolean indicating if the initialization was successful.
   */
  init() {
    return __async(this, arguments, function* (options = {}) {
      this.initServiceValues(options);
      const {
        config,
        initOptions
      } = options;
      this._instance = new Keycloak(config);
      this.bindsKeycloakEvents();
      const authenticated = yield this._instance.init(initOptions);
      if (authenticated && this._loadUserProfileAtStartUp) {
        yield this.loadUserProfile();
      }
      return authenticated;
    });
  }
  /**
   * Redirects to login form on (options is an optional object with redirectUri and/or
   * prompt fields).
   *
   * @param options
   * Object, where:
   *  - redirectUri: Specifies the uri to redirect to after login.
   *  - prompt:By default the login screen is displayed if the user is not logged-in to Keycloak.
   * To only authenticate to the application if the user is already logged-in and not display the
   * login page if the user is not logged-in, set this option to none. To always require
   * re-authentication and ignore SSO, set this option to login .
   *  - maxAge: Used just if user is already authenticated. Specifies maximum time since the
   * authentication of user happened. If user is already authenticated for longer time than
   * maxAge, the SSO is ignored and he will need to re-authenticate again.
   *  - loginHint: Used to pre-fill the username/email field on the login form.
   *  - action: If value is 'register' then user is redirected to registration page, otherwise to
   * login page.
   *  - locale: Specifies the desired locale for the UI.
   * @returns
   * A void Promise if the login is successful and after the user profile loading.
   */
  login() {
    return __async(this, arguments, function* (options = {}) {
      yield this._instance.login(options);
      if (this._loadUserProfileAtStartUp) {
        yield this.loadUserProfile();
      }
    });
  }
  /**
   * Redirects to logout.
   *
   * @param redirectUri
   * Specifies the uri to redirect to after logout.
   * @returns
   * A void Promise if the logout was successful, cleaning also the userProfile.
   */
  logout(redirectUri) {
    return __async(this, null, function* () {
      const options = {
        redirectUri
      };
      yield this._instance.logout(options);
      this._userProfile = void 0;
    });
  }
  /**
   * Redirects to registration form. Shortcut for login with option
   * action = 'register'. Options are same as for the login method but 'action' is set to
   * 'register'.
   *
   * @param options
   * login options
   * @returns
   * A void Promise if the register flow was successful.
   */
  register() {
    return __async(this, arguments, function* (options = {
      action: "register"
    }) {
      yield this._instance.register(options);
    });
  }
  /**
   * Check if the user has access to the specified role. It will look for roles in
   * realm and the given resource, but will not check if the user is logged in for better performance.
   *
   * @param role
   * role name
   * @param resource
   * resource name. If not specified, `clientId` is used
   * @returns
   * A boolean meaning if the user has the specified Role.
   */
  isUserInRole(role, resource) {
    let hasRole;
    hasRole = this._instance.hasResourceRole(role, resource);
    if (!hasRole) {
      hasRole = this._instance.hasRealmRole(role);
    }
    return hasRole;
  }
  /**
   * Return the roles of the logged user. The realmRoles parameter, with default value
   * true, will return the resource roles and realm roles associated with the logged user. If set to false
   * it will only return the resource roles. The resource parameter, if specified, will return only resource roles
   * associated with the given resource.
   *
   * @param realmRoles
   * Set to false to exclude realm roles (only client roles)
   * @param resource
   * resource name If not specified, returns roles from all resources
   * @returns
   * Array of Roles associated with the logged user.
   */
  getUserRoles(realmRoles = true, resource) {
    let roles = [];
    if (this._instance.resourceAccess) {
      Object.keys(this._instance.resourceAccess).forEach((key) => {
        if (resource && resource !== key) {
          return;
        }
        const resourceAccess = this._instance.resourceAccess[key];
        const clientRoles = resourceAccess["roles"] || [];
        roles = roles.concat(clientRoles);
      });
    }
    if (realmRoles && this._instance.realmAccess) {
      const realmRoles2 = this._instance.realmAccess["roles"] || [];
      roles.push(...realmRoles2);
    }
    return roles;
  }
  /**
   * Check if user is logged in.
   *
   * @returns
   * A boolean that indicates if the user is logged in.
   */
  isLoggedIn() {
    if (!this._instance) {
      return false;
    }
    return this._instance.authenticated;
  }
  /**
   * Returns true if the token has less than minValidity seconds left before
   * it expires.
   *
   * @param minValidity
   * Seconds left. (minValidity) is optional. Default value is 0.
   * @returns
   * Boolean indicating if the token is expired.
   */
  isTokenExpired(minValidity = 0) {
    return this._instance.isTokenExpired(minValidity);
  }
  /**
   * If the token expires within _updateMinValidity seconds the token is refreshed. If the
   * session status iframe is enabled, the session status is also checked.
   * Returns a promise telling if the token was refreshed or not. If the session is not active
   * anymore, the promise is rejected.
   *
   * @param minValidity
   * Seconds left. (minValidity is optional, if not specified updateMinValidity - default 20 is used)
   * @returns
   * Promise with a boolean indicating if the token was succesfully updated.
   */
  updateToken() {
    return __async(this, arguments, function* (minValidity = this._updateMinValidity) {
      if (this._silentRefresh) {
        if (this.isTokenExpired()) {
          throw new Error("Failed to refresh the token, or the session is expired");
        }
        return true;
      }
      if (!this._instance) {
        throw new Error("Keycloak Angular library is not initialized.");
      }
      try {
        return yield this._instance.updateToken(minValidity);
      } catch (error) {
        return false;
      }
    });
  }
  /**
   * Loads the user profile.
   * Returns promise to set functions to be invoked if the profile was loaded
   * successfully, or if the profile could not be loaded.
   *
   * @param forceReload
   * If true will force the loadUserProfile even if its already loaded.
   * @returns
   * A promise with the KeycloakProfile data loaded.
   */
  loadUserProfile(forceReload = false) {
    return __async(this, null, function* () {
      if (this._userProfile && !forceReload) {
        return this._userProfile;
      }
      if (!this._instance.authenticated) {
        throw new Error("The user profile was not loaded as the user is not logged in.");
      }
      return this._userProfile = yield this._instance.loadUserProfile();
    });
  }
  /**
   * Returns the authenticated token.
   */
  getToken() {
    return __async(this, null, function* () {
      return this._instance.token;
    });
  }
  /**
   * Returns the logged username.
   *
   * @returns
   * The logged username.
   */
  getUsername() {
    if (!this._userProfile) {
      throw new Error("User not logged in or user profile was not loaded.");
    }
    return this._userProfile.username;
  }
  /**
   * Clear authentication state, including tokens. This can be useful if application
   * has detected the session was expired, for example if updating token fails.
   * Invoking this results in onAuthLogout callback listener being invoked.
   */
  clearToken() {
    this._instance.clearToken();
  }
  /**
   * Adds a valid token in header. The key & value format is:
   * Authorization Bearer <token>.
   * If the headers param is undefined it will create the Angular headers object.
   *
   * @param headers
   * Updated header with Authorization and Keycloak token.
   * @returns
   * An observable with with the HTTP Authorization header and the current token.
   */
  addTokenToHeader(headers = new HttpHeaders()) {
    return from(this.getToken()).pipe(map((token) => token ? headers.set(this._authorizationHeaderName, this._bearerPrefix + token) : headers));
  }
  /**
   * Returns the original Keycloak instance, if you need any customization that
   * this Angular service does not support yet. Use with caution.
   *
   * @returns
   * The KeycloakInstance from keycloak-js.
   */
  getKeycloakInstance() {
    return this._instance;
  }
  /**
   * @deprecated
   * Returns the excluded URLs that should not be considered by
   * the http interceptor which automatically adds the authorization header in the Http Request.
   *
   * @returns
   * The excluded urls that must not be intercepted by the KeycloakBearerInterceptor.
   */
  get excludedUrls() {
    return this._excludedUrls;
  }
  /**
   * Flag to indicate if the bearer will be added to the authorization header.
   *
   * @returns
   * Returns if the bearer interceptor was set to be disabled.
   */
  get enableBearerInterceptor() {
    return this._enableBearerInterceptor;
  }
  /**
   * Keycloak subject to monitor the events triggered by keycloak-js.
   * The following events as available (as described at keycloak docs -
   * https://www.keycloak.org/docs/latest/securing_apps/index.html#callback-events):
   * - OnAuthError
   * - OnAuthLogout
   * - OnAuthRefreshError
   * - OnAuthRefreshSuccess
   * - OnAuthSuccess
   * - OnReady
   * - OnTokenExpire
   * In each occurrence of any of these, this subject will return the event type,
   * described at {@link KeycloakEventTypeLegacy} enum and the function args from the keycloak-js
   * if provided any.
   *
   * @returns
   * A subject with the {@link KeycloakEventLegacy} which describes the event type and attaches the
   * function args.
   */
  get keycloakEvents$() {
    return this._keycloakEvents$;
  }
  static {
    this.ɵfac = function KeycloakService_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _KeycloakService)();
    };
  }
  static {
    this.ɵprov = ɵɵdefineInjectable({
      token: _KeycloakService,
      factory: _KeycloakService.ɵfac
    });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(KeycloakService, [{
    type: Injectable
  }], null, null);
})();
var KeycloakBearerInterceptor = class _KeycloakBearerInterceptor {
  constructor() {
    this.keycloak = inject(KeycloakService);
  }
  /**
   * Calls to update the keycloak token if the request should update the token.
   *
   * @param req http request from @angular http module.
   * @returns
   * A promise boolean for the token update or noop result.
   */
  conditionallyUpdateToken(req) {
    return __async(this, null, function* () {
      if (this.keycloak.shouldUpdateToken(req)) {
        return yield this.keycloak.updateToken();
      }
      return true;
    });
  }
  /**
   * @deprecated
   * Checks if the url is excluded from having the Bearer Authorization
   * header added.
   *
   * @param req http request from @angular http module.
   * @param excludedUrlRegex contains the url pattern and the http methods,
   * excluded from adding the bearer at the Http Request.
   */
  isUrlExcluded({
    method,
    url
  }, {
    urlPattern,
    httpMethods
  }) {
    const httpTest = httpMethods.length === 0 || httpMethods.join().indexOf(method.toUpperCase()) > -1;
    const urlTest = urlPattern.test(url);
    return httpTest && urlTest;
  }
  /**
   * Intercept implementation that checks if the request url matches the excludedUrls.
   * If not, adds the Authorization header to the request if the user is logged in.
   *
   * @param req
   * @param next
   */
  intercept(req, next) {
    const {
      enableBearerInterceptor,
      excludedUrls
    } = this.keycloak;
    if (!enableBearerInterceptor) {
      return next.handle(req);
    }
    const shallPass = !this.keycloak.shouldAddToken(req) || excludedUrls.findIndex((item) => this.isUrlExcluded(req, item)) > -1;
    if (shallPass) {
      return next.handle(req);
    }
    return combineLatest([from(this.conditionallyUpdateToken(req)), of(this.keycloak.isLoggedIn())]).pipe(mergeMap(([_, isLoggedIn]) => isLoggedIn ? this.handleRequestWithTokenHeader(req, next) : next.handle(req)));
  }
  /**
   * Adds the token of the current user to the Authorization header
   *
   * @param req
   * @param next
   */
  handleRequestWithTokenHeader(req, next) {
    return this.keycloak.addTokenToHeader(req.headers).pipe(mergeMap((headersWithBearer) => {
      const kcReq = req.clone({
        headers: headersWithBearer
      });
      return next.handle(kcReq);
    }));
  }
  static {
    this.ɵfac = function KeycloakBearerInterceptor_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _KeycloakBearerInterceptor)();
    };
  }
  static {
    this.ɵprov = ɵɵdefineInjectable({
      token: _KeycloakBearerInterceptor,
      factory: _KeycloakBearerInterceptor.ɵfac
    });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(KeycloakBearerInterceptor, [{
    type: Injectable
  }], null, null);
})();
var CoreModule = class _CoreModule {
  static {
    this.ɵfac = function CoreModule_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _CoreModule)();
    };
  }
  static {
    this.ɵmod = ɵɵdefineNgModule({
      type: _CoreModule,
      imports: [CommonModule]
    });
  }
  static {
    this.ɵinj = ɵɵdefineInjector({
      providers: [KeycloakService, {
        provide: HTTP_INTERCEPTORS,
        useClass: KeycloakBearerInterceptor,
        multi: true
      }],
      imports: [CommonModule]
    });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(CoreModule, [{
    type: NgModule,
    args: [{
      imports: [CommonModule],
      providers: [KeycloakService, {
        provide: HTTP_INTERCEPTORS,
        useClass: KeycloakBearerInterceptor,
        multi: true
      }]
    }]
  }], null, null);
})();
var KeycloakAngularModule = class _KeycloakAngularModule {
  static {
    this.ɵfac = function KeycloakAngularModule_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _KeycloakAngularModule)();
    };
  }
  static {
    this.ɵmod = ɵɵdefineNgModule({
      type: _KeycloakAngularModule,
      imports: [CoreModule]
    });
  }
  static {
    this.ɵinj = ɵɵdefineInjector({
      imports: [CoreModule]
    });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(KeycloakAngularModule, [{
    type: NgModule,
    args: [{
      imports: [CoreModule]
    }]
  }], null, null);
})();
var KeycloakEventType;
(function(KeycloakEventType2) {
  KeycloakEventType2["KeycloakAngularNotInitialized"] = "KeycloakAngularNotInitialized";
  KeycloakEventType2["KeycloakAngularInit"] = "KeycloakAngularInit";
  KeycloakEventType2["AuthError"] = "AuthError";
  KeycloakEventType2["AuthLogout"] = "AuthLogout";
  KeycloakEventType2["AuthRefreshError"] = "AuthRefreshError";
  KeycloakEventType2["AuthRefreshSuccess"] = "AuthRefreshSuccess";
  KeycloakEventType2["AuthSuccess"] = "AuthSuccess";
  KeycloakEventType2["Ready"] = "Ready";
  KeycloakEventType2["TokenExpired"] = "TokenExpired";
  KeycloakEventType2["ActionUpdate"] = "ActionUpdate";
})(KeycloakEventType || (KeycloakEventType = {}));
var typeEventArgs = (args) => args;
var createKeycloakSignal = (keycloak) => {
  const keycloakSignal = signal({
    type: KeycloakEventType.KeycloakAngularInit
  }, ...ngDevMode ? [{
    debugName: "keycloakSignal"
  }] : []);
  if (!keycloak) {
    keycloakSignal.set({
      type: KeycloakEventType.KeycloakAngularNotInitialized
    });
    return keycloakSignal;
  }
  keycloak.onReady = (authenticated) => {
    keycloakSignal.set({
      type: KeycloakEventType.Ready,
      args: authenticated
    });
  };
  keycloak.onAuthError = (errorData) => {
    keycloakSignal.set({
      type: KeycloakEventType.AuthError,
      args: errorData
    });
  };
  keycloak.onAuthLogout = () => {
    keycloakSignal.set({
      type: KeycloakEventType.AuthLogout
    });
  };
  keycloak.onActionUpdate = (status, action) => {
    keycloakSignal.set({
      type: KeycloakEventType.ActionUpdate,
      args: {
        status,
        action
      }
    });
  };
  keycloak.onAuthRefreshError = () => {
    keycloakSignal.set({
      type: KeycloakEventType.AuthRefreshError
    });
  };
  keycloak.onAuthRefreshSuccess = () => {
    keycloakSignal.set({
      type: KeycloakEventType.AuthRefreshSuccess
    });
  };
  keycloak.onAuthSuccess = () => {
    keycloakSignal.set({
      type: KeycloakEventType.AuthSuccess
    });
  };
  keycloak.onTokenExpired = () => {
    keycloakSignal.set({
      type: KeycloakEventType.TokenExpired
    });
  };
  return keycloakSignal;
};
var KEYCLOAK_EVENT_SIGNAL = new InjectionToken("Keycloak Events Signal");
var HasRolesDirective = class _HasRolesDirective {
  constructor() {
    this.templateRef = inject(TemplateRef);
    this.viewContainer = inject(ViewContainerRef);
    this.keycloak = inject(Keycloak);
    this.roles = [];
    this.checkRealm = false;
    this.viewContainer.clear();
    const keycloakSignal = inject(KEYCLOAK_EVENT_SIGNAL);
    effect(() => {
      const keycloakEvent = keycloakSignal();
      switch (keycloakEvent.type) {
        case KeycloakEventType.Ready: {
          const authenticated = typeEventArgs(keycloakEvent.args);
          if (authenticated) {
            this.render();
          } else {
            this.viewContainer.clear();
          }
          break;
        }
        case KeycloakEventType.AuthSuccess:
        case KeycloakEventType.AuthRefreshSuccess:
        case KeycloakEventType.TokenExpired:
          this.render();
          break;
        case KeycloakEventType.AuthLogout:
          this.viewContainer.clear();
          break;
        default:
          break;
      }
    });
  }
  /**
   * Here to reevaluate access when inputs change.
   */
  ngOnChanges() {
    this.render();
  }
  /**
   * Clear the view and render it if user has access.
   */
  render() {
    const hasAccess = this.checkUserRoles();
    this.viewContainer.clear();
    if (hasAccess) {
      this.viewContainer.createEmbeddedView(this.templateRef);
    }
  }
  /**
   * Checks if the user has at least one of the specified roles in the resource or realm.
   * @returns True if the user has access, false otherwise.
   */
  checkUserRoles() {
    const hasResourceRole = this.roles.some((role) => this.keycloak.hasResourceRole(role, this.resource));
    const hasRealmRole = this.checkRealm ? this.roles.some((role) => this.keycloak.hasRealmRole(role)) : false;
    return hasResourceRole || hasRealmRole;
  }
  static {
    this.ɵfac = function HasRolesDirective_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _HasRolesDirective)();
    };
  }
  static {
    this.ɵdir = ɵɵdefineDirective({
      type: _HasRolesDirective,
      selectors: [["", "kaHasRoles", ""]],
      inputs: {
        roles: [0, "kaHasRoles", "roles"],
        resource: [0, "kaHasRolesResource", "resource"],
        checkRealm: [0, "kaHasRolesCheckRealm", "checkRealm"]
      },
      features: [ɵɵNgOnChangesFeature]
    });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(HasRolesDirective, [{
    type: Directive,
    args: [{
      selector: "[kaHasRoles]"
    }]
  }], () => [], {
    roles: [{
      type: Input,
      args: ["kaHasRoles"]
    }],
    resource: [{
      type: Input,
      args: ["kaHasRolesResource"]
    }],
    checkRealm: [{
      type: Input,
      args: ["kaHasRolesCheckRealm"]
    }]
  });
})();
var UserActivityService = class _UserActivityService {
  constructor() {
    this.lastActivity = signal(Date.now(), ...ngDevMode ? [{
      debugName: "lastActivity"
    }] : []);
    this.isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
    this.eventListeners = [];
    this.debounceTimeoutId = null;
    this.debounceTime = 300;
    this.lastActivitySignal = computed(() => this.lastActivity(), ...ngDevMode ? [{
      debugName: "lastActivitySignal"
    }] : []);
  }
  /**
   * Starts monitoring user activity events (`mousemove`, `touchstart`, `keydown`, `click`, `scroll`)
   * and updates the last activity timestamp using debouncing for performance optimization.
   */
  startMonitoring() {
    if (!this.isBrowser) {
      return;
    }
    const events = ["mousemove", "touchstart", "keydown", "click", "scroll"];
    const handler = () => this.debouncedUpdate();
    events.forEach((event) => {
      window.addEventListener(event, handler, {
        passive: true
      });
      this.eventListeners.push(() => window.removeEventListener(event, handler));
    });
  }
  /**
   * Updates the last activity timestamp with debounce.
   */
  debouncedUpdate() {
    if (this.debounceTimeoutId !== null) {
      clearTimeout(this.debounceTimeoutId);
    }
    this.debounceTimeoutId = setTimeout(() => {
      this.lastActivity.set(Date.now());
      this.debounceTimeoutId = null;
    }, this.debounceTime);
  }
  /**
   * Retrieves the timestamp of the last recorded user activity.
   * @returns {number} The last activity timestamp in milliseconds since epoch.
   */
  get lastActivityTime() {
    return this.lastActivity();
  }
  /**
   * Determines whether the user interacted with the application, meaning it is actively using the application, based on
   * the specified duration.
   * @param timeout - The inactivity timeout in milliseconds.
   * @returns {boolean} `true` if the user is inactive, otherwise `false`.
   */
  isActive(timeout) {
    return Date.now() - this.lastActivityTime < timeout;
  }
  /**
   * Cleans up event listeners and debouncing timer on destroy.
   * This method is automatically called by Angular when the service is removed.
   */
  ngOnDestroy() {
    this.eventListeners.forEach((remove) => remove());
    this.eventListeners = [];
    if (this.debounceTimeoutId !== null) {
      clearTimeout(this.debounceTimeoutId);
      this.debounceTimeoutId = null;
    }
  }
  static {
    this.ɵfac = function UserActivityService_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _UserActivityService)();
    };
  }
  static {
    this.ɵprov = ɵɵdefineInjectable({
      token: _UserActivityService,
      factory: _UserActivityService.ɵfac
    });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(UserActivityService, [{
    type: Injectable
  }], null, null);
})();
var AutoRefreshTokenService = class _AutoRefreshTokenService {
  constructor() {
    this.keycloak = inject(Keycloak);
    this.userActivity = inject(UserActivityService);
    this.options = this.defaultOptions;
    this.initialized = false;
    const keycloakSignal = inject(KEYCLOAK_EVENT_SIGNAL);
    effect(() => {
      const keycloakEvent = keycloakSignal();
      if (keycloakEvent.type === KeycloakEventType.TokenExpired) {
        this.processTokenExpiredEvent();
      }
    });
  }
  get defaultOptions() {
    return {
      sessionTimeout: 3e5,
      onInactivityTimeout: "logout",
      logoutOptions: void 0,
      loginOptions: void 0
    };
  }
  executeOnInactivityTimeout() {
    switch (this.options.onInactivityTimeout) {
      case "login":
        this.keycloak.login(this.options.loginOptions).catch((error) => console.error("Failed to execute the login call", error));
        break;
      case "logout":
        this.keycloak.logout(this.options.logoutOptions).catch((error) => console.error("Failed to execute the logout call", error));
        break;
      default:
        break;
    }
  }
  processTokenExpiredEvent() {
    if (!this.initialized || !this.keycloak.authenticated) {
      return;
    }
    if (this.userActivity.isActive(this.options.sessionTimeout)) {
      this.keycloak.updateToken().catch(() => this.executeOnInactivityTimeout());
    } else {
      this.executeOnInactivityTimeout();
    }
  }
  start(options) {
    this.options = __spreadValues(__spreadValues({}, this.defaultOptions), options);
    this.initialized = true;
    this.userActivity.startMonitoring();
  }
  static {
    this.ɵfac = function AutoRefreshTokenService_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _AutoRefreshTokenService)();
    };
  }
  static {
    this.ɵprov = ɵɵdefineInjectable({
      token: _AutoRefreshTokenService,
      factory: _AutoRefreshTokenService.ɵfac
    });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(AutoRefreshTokenService, [{
    type: Injectable
  }], () => [], null);
})();
function withAutoRefreshToken(options) {
  return {
    configure: () => {
      const autoRefreshTokenService = inject(AutoRefreshTokenService);
      autoRefreshTokenService.start(options);
    }
  };
}
var mapResourceRoles = (resourceAccess = {}) => {
  return Object.entries(resourceAccess).reduce((roles, [key, value]) => {
    roles[key] = value.roles;
    return roles;
  }, {});
};
var createAuthGuard = (isAccessAllowed) => {
  return (next, state) => {
    const keycloak = inject(Keycloak);
    const authenticated = keycloak?.authenticated ?? false;
    const grantedRoles = {
      resourceRoles: mapResourceRoles(keycloak?.resourceAccess),
      realmRoles: keycloak?.realmAccess?.roles ?? []
    };
    const authData = {
      authenticated,
      keycloak,
      grantedRoles
    };
    return isAccessAllowed(next, state, authData);
  };
};
var BEARER_PREFIX = "Bearer";
var AUTHORIZATION_HEADER_NAME = "Authorization";
var createInterceptorCondition = (value) => __spreadProps(__spreadValues({}, value), {
  bearerPrefix: value.bearerPrefix ?? BEARER_PREFIX,
  authorizationHeaderName: value.authorizationHeaderName ?? AUTHORIZATION_HEADER_NAME,
  shouldUpdateToken: value.shouldUpdateToken ?? (() => true)
});
var conditionallyUpdateToken = (_0, _1, _2) => __async(null, [_0, _1, _2], function* (req, keycloak, {
  shouldUpdateToken = (_) => true
}) {
  if (shouldUpdateToken(req)) {
    return yield keycloak.updateToken().catch(() => false);
  }
  return true;
});
var addAuthorizationHeader = (req, next, keycloak, condition) => {
  const {
    bearerPrefix = BEARER_PREFIX,
    authorizationHeaderName = AUTHORIZATION_HEADER_NAME
  } = condition;
  const clonedRequest = req.clone({
    setHeaders: {
      [authorizationHeaderName]: `${bearerPrefix} ${keycloak.token}`
    }
  });
  return next(clonedRequest);
};
var CUSTOM_BEARER_TOKEN_INTERCEPTOR_CONFIG = new InjectionToken("Include the bearer token as implemented by the provided function");
var customBearerTokenInterceptor = (req, next) => {
  const conditions = inject(CUSTOM_BEARER_TOKEN_INTERCEPTOR_CONFIG) ?? [];
  const keycloak = inject(Keycloak);
  return from(Promise.all(conditions.map((condition) => __async(null, null, function* () {
    return yield condition.shouldAddToken(req, next, keycloak);
  })))).pipe(mergeMap((evaluatedConditions) => {
    const matchingConditionIndex = evaluatedConditions.findIndex(Boolean);
    const matchingCondition = conditions[matchingConditionIndex];
    if (!matchingCondition) {
      return next(req);
    }
    return from(conditionallyUpdateToken(req, keycloak, matchingCondition)).pipe(mergeMap(() => keycloak.authenticated ? addAuthorizationHeader(req, next, keycloak, matchingCondition) : next(req)));
  }));
};
var INCLUDE_BEARER_TOKEN_INTERCEPTOR_CONFIG = new InjectionToken("Include the bearer token when explicitly defined int the URL pattern condition");
var findMatchingCondition = ({
  method,
  url
}, {
  urlPattern,
  httpMethods = []
}) => {
  const httpMethodTest = httpMethods.length === 0 || httpMethods.join().indexOf(method.toUpperCase()) > -1;
  const urlTest = urlPattern.test(url);
  return httpMethodTest && urlTest;
};
var includeBearerTokenInterceptor = (req, next) => {
  const conditions = inject(INCLUDE_BEARER_TOKEN_INTERCEPTOR_CONFIG) ?? [];
  const matchingCondition = conditions.find((condition) => findMatchingCondition(req, condition));
  if (!matchingCondition) {
    return next(req);
  }
  const keycloak = inject(Keycloak);
  return from(conditionallyUpdateToken(req, keycloak, matchingCondition)).pipe(mergeMap(() => keycloak.authenticated ? addAuthorizationHeader(req, next, keycloak, matchingCondition) : next(req)));
};
var provideKeycloakInAppInitializer = (keycloak, options) => {
  const {
    initOptions,
    features = []
  } = options;
  if (!initOptions) {
    return [];
  }
  return provideAppInitializer(() => __async(null, null, function* () {
    const injector = inject(EnvironmentInjector);
    runInInjectionContext(injector, () => features.forEach((feature) => feature.configure()));
    yield keycloak.init(initOptions).catch((error) => console.error("Keycloak initialization failed", error));
  }));
};
function provideKeycloak(options) {
  const keycloak = new Keycloak(options.config);
  const providers = options.providers ?? [];
  const keycloakSignal = createKeycloakSignal(keycloak);
  return makeEnvironmentProviders([{
    provide: KEYCLOAK_EVENT_SIGNAL,
    useValue: keycloakSignal
  }, {
    provide: Keycloak,
    useValue: keycloak
  }, ...providers, provideKeycloakInAppInitializer(keycloak, options)]);
}
export {
  AutoRefreshTokenService,
  CUSTOM_BEARER_TOKEN_INTERCEPTOR_CONFIG,
  CoreModule,
  HasRolesDirective,
  INCLUDE_BEARER_TOKEN_INTERCEPTOR_CONFIG,
  KEYCLOAK_EVENT_SIGNAL,
  KeycloakAngularModule,
  KeycloakAuthGuard,
  KeycloakBearerInterceptor,
  KeycloakEventType,
  KeycloakEventTypeLegacy,
  KeycloakService,
  UserActivityService,
  addAuthorizationHeader,
  conditionallyUpdateToken,
  createAuthGuard,
  createInterceptorCondition,
  createKeycloakSignal,
  customBearerTokenInterceptor,
  includeBearerTokenInterceptor,
  provideKeycloak,
  typeEventArgs,
  withAutoRefreshToken
};
//# sourceMappingURL=keycloak-angular.js.map
