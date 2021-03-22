// ---------------------------------------------------------------------
// dns collector configuration
// ---------------------------------------------------------------------
// Copyright (C) 2007-2021 The NOC Project
// See LICENSE for details
// ---------------------------------------------------------------------

use crate::zk::Configurable;
use serde::Deserialize;

#[derive(Deserialize, Debug)]
pub struct DNSConfig {
    pub query: String,
    #[serde(default = "default_type_a")]
    pub query_type: String,
    #[serde(default = "default_one")]
    pub n: usize,
    #[serde(default = "default_one")]
    pub min_success: usize,
}

impl Configurable<DNSConfig> for DNSConfig {}

fn default_type_a() -> String {
    "A".into()
}

fn default_one() -> usize {
    1
}
