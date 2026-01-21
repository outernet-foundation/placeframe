#include <DotNet/CesiumForUnity/CesiumUintMat2x2.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/CesiumForUnity/CesiumUintVec2.h>
#include <cstdint>

namespace DotNet::CesiumForUnity {
struct CesiumUintVec2;
}
namespace DotNet::CesiumForUnity {
struct CesiumUintMat2x2;
}

namespace DotNet::CesiumForUnity {

void (*CesiumUintMat2x2::Construct__GL6rL0hCqqkoxAtnbIobQ)(const ::DotNet::CesiumForUnity::CesiumUintVec2* v0, const ::DotNet::CesiumForUnity::CesiumUintVec2* v1, ::DotNet::CesiumForUnity::CesiumUintMat2x2* pReturnValue, void** reinteropException) = nullptr;


CesiumUintMat2x2 CesiumUintMat2x2::Construct(const ::DotNet::CesiumForUnity::CesiumUintVec2& v0, const ::DotNet::CesiumForUnity::CesiumUintVec2& v1)
{
    void* reinteropException = nullptr;
    CesiumUintMat2x2 result;
    Construct__GL6rL0hCqqkoxAtnbIobQ(&v0, &v1, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumUintMat2x2::Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumUintMat2x2* thiz, ::std::int32_t index, ::DotNet::CesiumForUnity::CesiumUintVec2* pReturnValue, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumUintVec2 CesiumUintMat2x2::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumUintVec2 result;
    Property_get_Item(&(*this), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::CesiumForUnity


