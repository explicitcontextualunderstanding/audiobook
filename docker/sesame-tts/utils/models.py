class SomeTransformerBackbone(nn.Module):
    def forward(self, tokens, input_pos=None, mask=None):
        # …existing code…
-        bsz, seq_len = tokens.shape
+        # allow tokens to have extra trailing dimensions
+        bsz, seq_len, *rest = tokens.shape
        # …existing code continues…
