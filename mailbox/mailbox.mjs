#!/usr/bin/env node
// Mailbox service CLI (issue #41): persists and correlates request-reply
// pairs. Unit-001 surface: register, dispatch, list, show. Reply submission
// and delivery arrive in later units — the record shape reserves their slots.

import { StoreError, exists, isPending, list, load, save, storeDir } from "./lib/store.mjs";

const STATUS_EXIT = { usage: 2, rejected: 3, notFound: 4 };

function usage() {
  return `mailbox — persist and correlate request-reply pairs (same host, same OS user)

Usage:
  mailbox register --id <requestId> --requester <identity> --worker <identity> --instruction <text>
  mailbox dispatch --id <requestId>
  mailbox list [--pending]
  mailbox show --id <requestId>

Environment:
  MAILBOX_DIR   store directory (default: ~/.local/share/mailbox)`;
}

function fail(code, message) {
  console.error(`mailbox: ${message}`);
  process.exit(code);
}

function parseArgs(argv) {
  const opts = {};
  const positional = [];
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (!arg.startsWith("--")) {
      positional.push(arg);
      continue;
    }
    if (arg === "--pending") { opts.pending = true; continue; }
    const value = argv[++i];
    if (value === undefined || value.startsWith("--")) fail(STATUS_EXIT.usage, `${arg} requires a value`);
    opts[arg.slice(2)] = value;
  }
  return { opts, positional };
}

function requireOpts(opts, names) {
  for (const name of names) {
    if (!opts[name]) fail(STATUS_EXIT.usage, `--${name} is required`);
  }
}

async function main(argv) {
  const [command, ...rest] = argv;
  const dir = storeDir();
  const { opts, positional } = parseArgs(rest);
  if (positional.length) fail(STATUS_EXIT.usage, `unexpected argument: ${positional[0]}`);

  switch (command) {
    case "register": {
      requireOpts(opts, ["id", "requester", "worker", "instruction"]);
      const requestId = opts.id;
      if (await exists(dir, requestId)) {
        // Re-registration with a live expectation is rejected; the original
        // request is left unchanged (feature scenario 2).
        fail(STATUS_EXIT.rejected, `request "${requestId}" already has a live expectation; registration rejected, original unchanged`);
      }
      const record = {
        requestId,
        requester: opts.requester,
        worker: opts.worker,
        instruction: opts.instruction,
        state: "pending", // pending | dispatched
        registeredAt: new Date().toISOString(),
        dispatchedAt: null,
        reply: null,
        delivered: false,
      };
      await save(dir, record);
      console.log(`registered ${requestId} (pending)`);
      break;
    }
    case "dispatch": {
      requireOpts(opts, ["id"]);
      const record = await load(dir, opts.id);
      if (!record) fail(STATUS_EXIT.notFound, `no request "${opts.id}"`);
      if (record.state === "dispatched") {
        console.log(`dispatched ${opts.id} (already dispatched; no-op)`);
        break;
      }
      record.state = "dispatched";
      record.dispatchedAt = new Date().toISOString();
      await save(dir, record);
      console.log(`dispatched ${opts.id}`);
      break;
    }
    case "list": {
      const records = await list(dir, { pendingOnly: Boolean(opts.pending) });
      for (const record of records) {
        console.log(`${record.requestId}\t${record.state}\t${isPending(record) ? "no-outcome" : "has-outcome"}`);
      }
      break;
    }
    case "show": {
      requireOpts(opts, ["id"]);
      const record = await load(dir, opts.id);
      if (!record) fail(STATUS_EXIT.notFound, `no request "${opts.id}"`);
      console.log(JSON.stringify(record, null, 2));
      break;
    }
    default:
      fail(STATUS_EXIT.usage, `unknown command: ${command ?? "(none)"}\n\n${usage()}`);
  }
}

main(process.argv.slice(2)).catch((err) => {
  if (err instanceof StoreError) {
    console.error(`mailbox: ${err.message}`);
    process.exit(STATUS_EXIT.usage);
  }
  throw err;
});
