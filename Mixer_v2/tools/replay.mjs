/**
 * Reapply preserved copper through an already connected MCP client.
 *
 * In a separate workspace copy, copy Balanced.unrouted.json to Balanced.pcb
 * and Mixer.unrouted.json to Mixer.pcb; keep Base/ intact. Open and replay
 * Balanced first, save it, then open/reload Mixer and replay Mixer.
 *
 * await replay(client, documentId, JSON.parse(await readFile(copperPath)));
 * client implements the standard MCP callTool({name, arguments}) method.
 * The original routed files must not be used as replay destinations.
 */
export async function replay(client, documentId, copper) {
  async function call(name, args) {
    const result = await client.callTool({name: `xcopper_${name}`, arguments: args});
    const data = result.structuredContent ?? JSON.parse(result.content.find(c => c.type === 'text').text);
    if (result.isError || data.error) throw new Error(JSON.stringify(data.error ?? data));
    return data;
  }
  let design = await call('get_design', {documentId});
  if (design.traces.some(t => !t.readOnly) || design.vias.some(v => !v.readOnly)) {
    throw new Error('Replay requires an unrouted destination without native copper.');
  }
  let revision = design.revision;
  const operations = [
    ...copper.vias.map(v => ({tool: 'place_via', arguments: {at: v.at, net: v.net}})),
    ...copper.traces.map(t => ({tool: 'route_traces', arguments: {
      points: [t.start, t.end], layer: t.layer, width: t.width, net: t.net
    }}))
  ];
  for (let start = 0; start < operations.length; start += 100) {
    const result = await call('apply_edits', {
      documentId, expectedRevision: revision, name: 'Replay preserved copper',
      operations: operations.slice(start, start + 100), response: 'compact'
    });
    revision = result.revision;
  }
  const check = await call('check_design', {documentId});
  if (check.violations.length || check.connections.length || check.moduleErrors.length || check.schematicDiagnostics.length) {
    throw new Error(`Replay requires review: ${JSON.stringify(check)}`);
  }
  await call('save_document', {documentId, response: 'compact'});
  return check;
}
