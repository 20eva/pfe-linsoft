import express from 'express';
import cors from 'cors';
import * as bodyParser from 'body-parser';
import routes from './app/routes/routes';
import HttpException from './app/models/http-exception.model';

const app = express();

/**
 * App Configuration
 */

app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(routes);

// Serves images
app.use(express.static(__dirname + '/assets'));

app.get('/', (req: express.Request, res: express.Response) => {
  res.json({ status: 'API is running on /api' });
});

/* eslint-disable */
app.use(
  (
    err: Error | HttpException,
    req: express.Request,
    res: express.Response,
    next: express.NextFunction,
  ) => {
    // @ts-ignore
    if (err && err.name === 'UnauthorizedError') {
      return res.status(401).json({
        status: 'error',
        message: 'missing authorization credentials',
      });
      // @ts-ignore
    } else if (err && err.errorCode) {
      // @ts-ignore
      res.status(err.errorCode).json(err.message);
    } else if (err) {
      res.status(500).json(err.message);
    }
  },
);

/**
 * Server activation
 */

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.info(`server up on port ${PORT}`);
});
// Demo Tue Aug  4 04:50:43 PM CET 2026
// Demo trigger Tue Aug  4 09:01:18 PM CET 2026
// Webhook test Tue Aug  4 09:10:35 PM CET 2026
// Final demo test Tue Aug  4 10:20:39 PM CET 2026
// Bore tunnel test Wed Aug  5 07:59:18 AM CET 2026
// Demo Wed Aug  5 08:27:44 AM CET 2026
// Demo ready Wed Aug  5 08:40:25 AM CET 2026
// E2E test Fri Aug  7 10:32:54 AM CET 2026
// Full pipeline test with build Fri Aug  7 10:48:44 AM CET 2026
// Full pipeline test Fri Aug  7 11:19:45 AM CET 2026
// Full pipeline test Fri Aug  7 12:40:30 PM CET 2026
// Auto trigger test Fri Aug  7 12:54:42 PM CET 2026
// bore fixed port 9000 Fri Aug  7 01:00:32 PM CET 2026
// registry push fix Fri Aug  7 01:12:17 PM CET 2026
// timeout fix test Fri Aug  7 02:23:22 PM CET 2026
// registry auth fix Fri Aug  7 02:48:04 PM CET 2026
// kaniko test Fri Aug  7 03:14:01 PM CET 2026
// registry hostname fix Fri Aug  7 03:21:13 PM CET 2026
// pipeline-sa fix Fri Aug  7 03:32:04 PM CET 2026
// kaniko config.json fix Fri Aug  7 03:39:54 PM CET 2026
// full pipeline with deploy Fri Aug  7 04:35:51 PM CET 2026
// clean build fix Fri Aug  7 04:41:39 PM CET 2026
// buildah fresh token Fri Aug  7 04:50:40 PM CET 2026
// new sonar token Fri Aug  7 05:10:46 PM CET 2026
// sonar fix Fri Aug  7 05:19:05 PM CET 2026
// sonar pinned version Fri Aug  7 05:29:34 PM CET 2026
// sonar internal url Fri Aug  7 05:39:08 PM CET 2026
// sonar cd fix Fri Aug  7 05:48:57 PM CET 2026
// fresh sonar token Sat Aug  8 03:12:39 PM CET 2026
// hardcoded token Sat Aug  8 03:17:13 PM CET 2026
// scanner config override Sat Aug  8 03:24:23 PM CET 2026
// cache clear fix Sat Aug  8 03:29:33 PM CET 2026
