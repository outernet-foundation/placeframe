#include <DotNet/CesiumForUnity/CesiumIntMat2x2.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/CesiumForUnity/CesiumIntVec2.h>
#include <cstdint>

namespace DotNet::CesiumForUnity {
struct CesiumIntVec2;
}
namespace DotNet::CesiumForUnity {
struct CesiumIntMat2x2;
}

namespace DotNet::CesiumForUnity {

void (*CesiumIntMat2x2::Construct_FoRlw9gqeGSV1ZBPJBNk9g)(const ::DotNet::CesiumForUnity::CesiumIntVec2* v0, const ::DotNet::CesiumForUnity::CesiumIntVec2* v1, ::DotNet::CesiumForUnity::CesiumIntMat2x2* pReturnValue, void** reinteropException) = nullptr;


CesiumIntMat2x2 CesiumIntMat2x2::Construct(const ::DotNet::CesiumForUnity::CesiumIntVec2& v0, const ::DotNet::CesiumForUnity::CesiumIntVec2& v1)
{
    void* reinteropException = nullptr;
    CesiumIntMat2x2 result;
    Construct_FoRlw9gqeGSV1ZBPJBNk9g(&v0, &v1, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumIntMat2x2::Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumIntMat2x2* thiz, ::std::int32_t index, ::DotNet::CesiumForUnity::CesiumIntVec2* pReturnValue, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumIntVec2 CesiumIntMat2x2::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumIntVec2 result;
    Property_get_Item(&(*this), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::CesiumForUnity


