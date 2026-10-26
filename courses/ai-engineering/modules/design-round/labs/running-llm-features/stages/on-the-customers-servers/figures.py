def figures():
    servers, gpu_gb, peak = 2, 24, 40
    params, weight_bits = 8, 4
    layers, kv_heads, head_dim, cache_bytes = 32, 8, 128, 2
    context, short_context, reserve_gb = 8_000, 6_000, 2

    weights_gb = params * weight_bits / 8
    kv_token = 2 * layers * kv_heads * head_dim * cache_bytes
    free_gb = servers * (gpu_gb - weights_gb - reserve_gb)

    def gb(count):
        return f"{count / 1e9:.1f} GB"

    def fit(tokens):
        return int(free_gb * 1e9 // (kv_token * tokens))

    return {
        "servers": str(servers),
        "gpu_gb": str(gpu_gb),
        "peak": str(peak),
        "params": str(params),
        "weight_bits": str(weight_bits),
        "layers": str(layers),
        "kv_heads": str(kv_heads),
        "head_dim": str(head_dim),
        "cache_bytes": str(cache_bytes),
        "context": f"{context:,}",
        "short_context": f"{short_context:,}",
        "weights_gb": f"{weights_gb:.0f} GB",
        "double_weights_gb": f"{2 * weights_gb:.0f} GB",
        "kv_token": f"{kv_token:,}",
        "kv_user": gb(kv_token * context),
        "kv_peak": gb(kv_token * context * peak),
        "total_gb": f"{servers * gpu_gb} GB",
        "reserve_gb": f"{reserve_gb} GB",
        "free_gb": f"{free_gb:.0f} GB",
        "fit_full": str(fit(context)),
        "fit_short": str(fit(short_context)),
    }
