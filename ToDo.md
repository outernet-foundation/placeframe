# To Do

## Capture App

- [x] Cache domain/username/password (encrypt?)
  - Should VisualPositioningSystem.Login automatically append "/auth/realms/placeframe-dev/protocol/openid-connect/token"?
- [x] Default domain/username/password to our usual defaults
- [] ~~Add "keep me logged in" toggle~~
- [] Investigate why removing local files leads to an error (doing this should also leave the info screen)
- [] Investigate why creating a map after reconstructing (in the same session) fails

## Map Registration App

- [x] Cache domain/username/password (encrypt?)
- [x] Default domain/username/password to our usual defaults
- [] ~~Add "keep me logged in" toggle~~
- [] Create mac/windows build

## Magic Leap Client

- [] Investigate localization instability (motion blur?)

## Android Client

- [] Holding phone in landscape breaks localization

## Capture App

- [] Holding phone in landscape breaks localization

## Any Client

- [] Align down vectors of unity and any incoming localizations (low priority)
- [] Smoothing and confidence between localizations
- [] Cesium credits are currently violating their TOS- read through this and figure out how to serve them correctly
