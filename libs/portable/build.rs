fn main() {
    let target_os = std::env::var("CARGO_CFG_TARGET_OS").unwrap_or_default();
    if target_os == "windows" {
        use std::io::Write;
        let mut res = winres::WindowsResource::new();
        if std::env::consts::OS != "windows" {
            res.set_toolkit_path("/usr/bin");
            res.set_windres_path("x86_64-w64-mingw32-windres");
            res.set_ar_path("x86_64-w64-mingw32-ar");
        }
        res.set_icon("../../res/icon.ico")
            .set_language(0x0409)
            .set_manifest_file("../../res/manifest.xml");
        match res.compile() {
            Err(e) => {
                write!(std::io::stderr(), "{}", e).unwrap();
                std::process::exit(1);
            }
            Ok(_) => {
                // Cuando se compila con MinGW / GNU ld, ld puede descartar libresource.a
                // si no hay símbolos referenciados. Pasar directamente resource.o garantiza
                // que la sección .rsrc con el icono se incruste obligatoriamente en el PE.
                if let Ok(out_dir) = std::env::var("OUT_DIR") {
                    let res_obj = std::path::Path::new(&out_dir).join("resource.o");
                    if res_obj.exists() {
                        println!("cargo:rustc-link-arg={}", res_obj.display());
                    }
                }
            }
        }
    }
}
