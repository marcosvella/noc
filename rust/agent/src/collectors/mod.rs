// ---------------------------------------------------------------------
// collectors
// ---------------------------------------------------------------------
// Copyright (C) 2007-2021 The NOC Project
// See LICENSE for details
// ---------------------------------------------------------------------

pub mod base;
#[cfg(feature = "dns")]
pub mod dns;
mod registry;
#[cfg(feature = "test")]
pub mod test;
#[cfg(feature = "twamp-reflector")]
pub mod twamp_reflector;
#[cfg(feature = "twamp-sender")]
pub mod twamp_sender;

pub use base::{Collectable, Collector, Configurable, Runnable, Status};
pub use registry::CollectorConfig;
